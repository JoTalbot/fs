import hashlib
import json
import multiprocessing
from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import WorkspaceTransfer, plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_journal import TransferJournalPhase, WorkspaceTransferJournal
from fs_overlay.workspace_transfer_recovery import (
    DestinationRecoveryState,
    RecoveryDecision,
    TransferRecoveryEvidence,
    TransferRecoveryPlan,
    reconcile_materializing_transaction,
)
from fs_overlay.workspace_transfer_recovery_audit import (
    RecoveryAuditCorruption,
    RecoveryAuditLog,
    RecoveryAuditTransition,
)


def _plan(decision: RecoveryDecision = RecoveryDecision.MANUAL_REVIEW, transaction_id: str = "tx-1") -> TransferRecoveryPlan:
    return TransferRecoveryPlan(
        transaction_id=transaction_id,
        operation=WorkspaceTransfer.IMPORT,
        snapshot_id="snapshot-1",
        decision=decision,
        reason="explicit test evidence",
    )


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
    return TransferRecoveryEvidence(
        transaction_id=candidate.transaction_id,
        snapshot_id=candidate.snapshot_id,
        destination_state=DestinationRecoveryState.MATCHES_SNAPSHOT,
        destination_verified=True,
        mutation_complete=True,
        source_preserved=True,
        rollback_safe=False,
        staging_absent=True,
    )


def _append_audit_worker(path: str, transaction_id: str, ready, start) -> None:
    log = RecoveryAuditLog(path)
    ready.set()
    start.wait(5)
    log.append(_plan(transaction_id=transaction_id), TransferJournalPhase.MATERIALIZING)


def test_audit_records_decision_without_granting_authority(tmp_path: Path) -> None:
    log = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    event = log.append(_plan(RecoveryDecision.COMMIT_PROVEN), TransferJournalPhase.MATERIALIZING)
    assert event.decision is RecoveryDecision.COMMIT_PROVEN
    assert event.proposed_transition is RecoveryAuditTransition.COMMIT
    assert log.replay() == (event,)


def test_audit_records_manual_review_as_non_mutating_transition(tmp_path: Path) -> None:
    log = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    event = log.append(_plan(), TransferJournalPhase.MATERIALIZING)
    assert event.proposed_transition is RecoveryAuditTransition.MANUAL_REVIEW
    assert event.previous_digest is None


def test_audit_hash_chain_and_sequence_are_durable(tmp_path: Path) -> None:
    log = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    first = log.append(_plan(), TransferJournalPhase.MATERIALIZING)
    second = log.append(_plan(RecoveryDecision.ABORT_PROVEN), TransferJournalPhase.MATERIALIZING)
    assert second.sequence == 2
    assert second.previous_digest == first.event_digest
    assert log.replay() == (first, second)


def test_audit_reopen_replays_and_continues_hash_chain(tmp_path: Path) -> None:
    path = tmp_path / "recovery-audit.log"
    first_log = RecoveryAuditLog(path)
    first = first_log.append(_plan(), TransferJournalPhase.MATERIALIZING)
    reopened_log = RecoveryAuditLog(path)
    assert reopened_log.replay() == (first,)
    second = reopened_log.append(_plan(RecoveryDecision.ABORT_PROVEN), TransferJournalPhase.MATERIALIZING)
    assert second.sequence == 2
    assert second.previous_digest == first.event_digest
    assert RecoveryAuditLog(path).replay() == (first, second)


def test_recovery_decision_and_audit_do_not_advance_reopened_journal(tmp_path: Path) -> None:
    _, journal = _materializing_candidate(tmp_path)
    reopened_journal = WorkspaceTransferJournal(journal.path)
    candidate = reopened_journal.recovery_candidates()[0]
    recovery = reconcile_materializing_transaction(candidate, _complete_commit_evidence(candidate))
    assert recovery.decision is RecoveryDecision.COMMIT_PROVEN
    audit = RecoveryAuditLog(tmp_path / "recovery-audit.log")
    event = audit.append(recovery, candidate.phase)
    assert event.proposed_transition is RecoveryAuditTransition.COMMIT
    assert tuple(reopened_journal.replay())[-1].phase is TransferJournalPhase.MATERIALIZING
    assert reopened_journal.recovery_candidates() == (candidate,)
    assert RecoveryAuditLog(audit.path).replay() == (event,)


def test_recovery_decision_and_audit_replay_remain_evidence_only_after_reopen(tmp_path: Path) -> None:
    _, journal = _materializing_candidate(tmp_path)
    candidate = WorkspaceTransferJournal(journal.path).recovery_candidates()[0]
    recovery = reconcile_materializing_transaction(candidate, _complete_commit_evidence(candidate))
    audit_path = tmp_path / "recovery-audit.log"
    RecoveryAuditLog(audit_path).append(recovery, candidate.phase)
    reopened_journal = WorkspaceTransferJournal(journal.path)
    reopened_audit = RecoveryAuditLog(audit_path)
    assert reopened_journal.recovery_candidates() == (candidate,)
    assert reopened_audit.replay()[0].decision is RecoveryDecision.COMMIT_PROVEN
    assert reopened_audit.replay()[0].proposed_transition is RecoveryAuditTransition.COMMIT
    assert tuple(reopened_journal.replay())[-1].phase is TransferJournalPhase.MATERIALIZING


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
    log.append(_plan(), TransferJournalPhase.MATERIALIZING)
    with path.open("ab") as handle:
        handle.write(b'{"version":1')
    with pytest.raises(RecoveryAuditCorruption, match="incomplete record"):
        log.replay()


def test_audit_rejects_tampered_event(tmp_path: Path) -> None:
    path = tmp_path / "recovery-audit.log"
    log = RecoveryAuditLog(path)
    log.append(_plan(), TransferJournalPhase.MATERIALIZING)
    raw = path.read_text().replace("explicit test evidence", "tampered evidence")
    path.write_text(raw)
    with pytest.raises(RecoveryAuditCorruption, match="digest mismatch"):
        log.replay()


def test_audit_rejects_broken_chain_even_when_event_digest_is_repaired(tmp_path: Path) -> None:
    path = tmp_path / "recovery-audit.log"
    log = RecoveryAuditLog(path)
    first = log.append(_plan(), TransferJournalPhase.MATERIALIZING)
    second = log.append(_plan(RecoveryDecision.ABORT_PROVEN), TransferJournalPhase.MATERIALIZING)
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
        log.append(_plan(), TransferJournalPhase.PREPARED)
