import hashlib
import json
from pathlib import Path

import pytest

from fs_overlay.workspace_migration import WorkspaceTransfer
from fs_overlay.workspace_transfer_journal import TransferJournalPhase
from fs_overlay.workspace_transfer_recovery import RecoveryDecision, TransferRecoveryPlan
from fs_overlay.workspace_transfer_recovery_audit import (
    RecoveryAuditCorruption,
    RecoveryAuditLog,
    RecoveryAuditTransition,
)


def _plan(decision: RecoveryDecision = RecoveryDecision.MANUAL_REVIEW) -> TransferRecoveryPlan:
    return TransferRecoveryPlan(
        transaction_id="tx-1",
        operation=WorkspaceTransfer.IMPORT,
        snapshot_id="snapshot-1",
        decision=decision,
        reason="explicit test evidence",
    )


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
    record["event_digest"] = ""
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
