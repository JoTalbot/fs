import hashlib
import json
import multiprocessing
from dataclasses import replace
from pathlib import Path

import pytest

from fs_overlay.recovery_preflight import RecoveryPreflightResult, recovery_preflight
from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import WorkspaceTransfer, plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_journal import (
    TransferJournalEntry,
    TransferJournalPhase,
    WorkspaceTransferJournal,
)
from fs_overlay.workspace_transfer_recovery import (
    DestinationRecoveryState,
    RecoveryDecision,
    TransferRecoveryEvidence,
    TransferRecoveryPlan,
    reconcile_materializing_transaction,
    recovery_evidence_digest,
)
from fs_overlay.workspace_transfer_recovery_audit import (
    RecoveryAuditCorruption,
    RecoveryAuditLog,
    RecoveryAuditTransition,
)


class _VerifiedEvidence:
    def verify(self, transaction, evidence):
        return True


def _entry(transaction_id: str = "tx-1") -> TransferJournalEntry:
    return TransferJournalEntry(
        transaction_id,
        TransferJournalPhase.MATERIALIZING,
        WorkspaceTransfer.IMPORT,
        "snapshot-1",
        "source",
        "destination",
    )


def _evidence(
    *,
    transaction_id: str = "tx-1",
    destination_state: DestinationRecoveryState = DestinationRecoveryState.UNKNOWN,
    destination_verified: bool = False,
    mutation_complete: bool = False,
    source_preserved: bool = True,
    rollback_safe: bool = False,
    staging_absent: bool = False,
) -> TransferRecoveryEvidence:
    return TransferRecoveryEvidence(
        transaction_id=transaction_id,
        snapshot_id="snapshot-1",
        destination_state=destination_state,
        destination_verified=destination_verified,
        mutation_complete=mutation_complete,
        source_preserved=source_preserved,
        rollback_safe=rollback_safe,
        staging_absent=staging_absent,
    )


def _verified_result(
    decision: RecoveryDecision = RecoveryDecision.MANUAL_REVIEW,
    evidence: TransferRecoveryEvidence | None = None,
    transaction_id: str = "tx-1",
) -> RecoveryPreflightResult:
    entry = _entry(transaction_id)
    evidence = evidence or _evidence(transaction_id=transaction_id)
    plan = reconcile_materializing_transaction(entry, evidence)
    if plan.decision is not decision:
        raise AssertionError(f"expected {decision}, got {plan.decision}")
    return recovery_preflight(entry, evidence, evidence_verifier=_VerifiedEvidence())


def _materializing_candidate(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "destination"
    destination.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    engine.put(b"payload")
    state = WorkspaceStateStore(tmp_path / "snapshots").create(
        WorkspaceBinding("source", str(source), owned_or_delegated=True), engine
    )
    plan = plan_import(
        state,
        WorkspaceBinding("destination", str(destination), owned_or_delegated=True),
    )
    journal = WorkspaceTransferJournal(tmp_path / "transfer-journal.log")
    transaction_id = journal.begin(plan)
    journal.mark(transaction_id, plan, TransferJournalPhase.MATERIALIZING)
    return plan, journal


def _complete_commit_evidence(candidate) -> TransferRecoveryEvidence:
    return _evidence(
        transaction_id=candidate.transaction_id,
        destination_state=DestinationRecoveryState.MATCHES_SNAPSHOT,
        destination_verified=True,
        mutation_complete=True,
        staging_absent=True,
    )


def _append_audit_worker(path: str, transaction_id: str, ready, start) -> None:
    log = RecoveryAuditLog(path)
    ready.set()
    start.wait(5)
    log.append(_verified_result(transaction_id=transaction_id), TransferJournalPhase.MATERIALIZING)


def test_evidence_digest_covers_every_evidence_field() -> None:
    base = _evidence()
    fields = (
        "destination_state",
        "destination_verified",
        "mutation_complete",
        "source_preserved",
        "rollback_safe",
        "staging_absent",
    )
    variants = (
        replace(base, destination_state=DestinationRecoveryState.ABSENT),
        replace(base, destination_verified=True),
        replace(base, mutation_complete=True),
        replace(base, source_preserved=False),
        replace(base, rollback_safe=True),
        replace(base, staging_absent=True),
    )
    assert all(recovery_evidence_digest(base) != recovery_evidence_digest(item) for item in variants)
    assert len(fields) == len(variants)


def test_audit_requires_verified_preflight_result(tmp_path: Path) -> None:
    log = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    plan = TransferRecoveryPlan("tx-1", WorkspaceTransfer.IMPORT, "snapshot-1", RecoveryDecision.MANUAL_REVIEW, "test")
    with pytest.raises(AttributeError):
        log.append(plan, TransferJournalPhase.MATERIALIZING)


def test_audit_binds_exact_verified_evidence_digest(tmp_path: Path) -> None:
    log = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    evidence = _evidence()
    result = _verified_result(evidence=evidence)
    event = log.append(result, result.transaction.phase)
    assert event.evidence_digest == recovery_evidence_digest(evidence)
    assert event.evidence_digest == result.evidence_digest


def test_audit_rejects_result_with_mutated_evidence_digest(tmp_path: Path) -> None:
    log = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    result = _verified_result()
    forged = replace(result, evidence_digest="0" * 64)
    with pytest.raises(ValueError, match="evidence digest mismatch"):
        log.append(forged, result.transaction.phase)


def test_audit_records_decision_without_granting_authority(tmp_path: Path) -> None:
    log = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    result = _verified_result()
    event = log.append(result, result.transaction.phase)
    assert event.decision is RecoveryDecision.MANUAL_REVIEW
    assert event.proposed_transition is RecoveryAuditTransition.MANUAL_REVIEW
    assert log.replay() == (event,)


def test_audit_hash_chain_and_sequence_are_durable(tmp_path: Path) -> None:
    log = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    first = log.append(_verified_result(), TransferJournalPhase.MATERIALIZING)
    second = log.append(_verified_result(RecoveryDecision.ABORT_PROVEN, _evidence(destination_state=DestinationRecoveryState.ABSENT, rollback_safe=True, staging_absent=True)), TransferJournalPhase.MATERIALIZING)
    assert second.sequence == 2
    assert second.previous_digest == first.event_digest
    assert log.replay() == (first, second)


def test_recovery_decision_and_audit_do_not_advance_reopened_journal(tmp_path: Path) -> None:
    _, journal = _materializing_candidate(tmp_path)
    candidate = WorkspaceTransferJournal(journal.path).recovery_candidates()[0]
    recovery = recovery_preflight(candidate, _complete_commit_evidence(candidate), evidence_verifier=_VerifiedEvidence())
    audit = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    event = audit.append(recovery, candidate.phase)
    assert event.proposed_transition is RecoveryAuditTransition.COMMIT
    assert tuple(journal.replay())[-1].phase is TransferJournalPhase.MATERIALIZING
    assert journal.recovery_candidates() == (candidate,)


def test_audit_serializes_cross_process_appends(tmp_path: Path) -> None:
    path = tmp_path / "recovery-audit.log"
    ctx = multiprocessing.get_context("spawn")
    start = ctx.Event()
    ready_a = ctx.Event()
    ready_b = ctx.Event()
    processes = [
        ctx.Process(target=_append_audit_worker, args=(str(path), "tx-a", ready_a, start)),
        ctx.Process(target=_append_audit_worker, args=(str(path), "tx-b", ready_b, start)),
    ]
    for process in processes:
        process.start()
    try:
        assert ready_a.wait(5)
        assert ready_b.wait(5)
        start.set()
        for process in processes:
            process.join(timeout=10)
        assert all(process.exitcode == 0 for process in processes)
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
    events = RecoveryAuditLog(path).replay()
    assert len(events) == 2
    assert [event.sequence for event in events] == [1, 2]
    assert {event.transaction_id for event in events} == {"tx-a", "tx-b"}
    assert events[1].previous_digest == events[0].event_digest


def test_audit_rejects_incomplete_tail_record(tmp_path: Path) -> None:
    path = tmp_path / "recovery-audit.log"
    log = RecoveryAuditLog(path)
    log.append(_verified_result(), TransferJournalPhase.MATERIALIZING)
    with path.open("ab") as handle:
        handle.write(b'{"version":1')
    with pytest.raises(RecoveryAuditCorruption, match="incomplete record"):
        log.replay()


def test_audit_rejects_tampered_event(tmp_path: Path) -> None:
    path = tmp_path / "recovery-audit.log"
    log = RecoveryAuditLog(path)
    log.append(_verified_result(), TransferJournalPhase.MATERIALIZING)
    raw = path.read_text().replace("manual_review", "commit")
    path.write_text(raw)
    with pytest.raises(RecoveryAuditCorruption, match="digest mismatch"):
        log.replay()


def test_audit_rejects_broken_chain_even_when_event_digest_is_repaired(tmp_path: Path) -> None:
    path = tmp_path / "recovery-audit.log"
    log = RecoveryAuditLog(path)
    first = log.append(_verified_result(), TransferJournalPhase.MATERIALIZING)
    second = log.append(_verified_result(), TransferJournalPhase.MATERIALIZING)
    lines = path.read_text().splitlines()
    record = json.loads(lines[1])
    record["previous_digest"] = "0" * 64
    record["event_digest"] = None
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    record["event_digest"] = hashlib.sha256(encoded).hexdigest()
    lines[1] = json.dumps(record, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n")
    assert second.previous_digest == first.event_digest
    with pytest.raises(RecoveryAuditCorruption, match="hash chain"):
        log.replay()


def test_audit_rejects_non_materializing_phase(tmp_path: Path) -> None:
    log = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    with pytest.raises(ValueError, match="materializing"):
        log.append(_verified_result(), TransferJournalPhase.PREPARED)
