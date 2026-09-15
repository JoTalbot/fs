from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_journal import TransferJournalPhase, WorkspaceTransferJournal
from fs_overlay.workspace_transfer_recovery import (
    DestinationRecoveryState,
    RecoveryDecision,
    TransferRecoveryEvidence,
    reconcile_materializing_transaction,
)


def _candidate(tmp_path: Path):
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
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    journal.mark(transaction_id, plan, TransferJournalPhase.MATERIALIZING)
    return journal.recovery_candidates()[0]


def _evidence(entry, **overrides):
    values = {
        "transaction_id": entry.transaction_id,
        "snapshot_id": entry.snapshot_id,
        "destination_state": DestinationRecoveryState.UNKNOWN,
        "destination_verified": False,
        "mutation_complete": False,
        "source_preserved": True,
        "rollback_safe": False,
    }
    values.update(overrides)
    return TransferRecoveryEvidence(**values)


def test_recovery_proves_commit_only_from_complete_matching_evidence(tmp_path: Path) -> None:
    entry = _candidate(tmp_path)
    plan = reconcile_materializing_transaction(
        entry,
        _evidence(
            entry,
            destination_state=DestinationRecoveryState.MATCHES_SNAPSHOT,
            destination_verified=True,
            mutation_complete=True,
        ),
    )
    assert plan.decision is RecoveryDecision.COMMIT_PROVEN


def test_recovery_proves_abort_only_when_destination_absent_and_rollback_safe(tmp_path: Path) -> None:
    entry = _candidate(tmp_path)
    plan = reconcile_materializing_transaction(
        entry,
        _evidence(
            entry,
            destination_state=DestinationRecoveryState.ABSENT,
            rollback_safe=True,
        ),
    )
    assert plan.decision is RecoveryDecision.ABORT_PROVEN


def test_recovery_fails_closed_on_unknown_or_conflicting_evidence(tmp_path: Path) -> None:
    entry = _candidate(tmp_path)
    for state in (DestinationRecoveryState.UNKNOWN, DestinationRecoveryState.CONFLICTING):
        plan = reconcile_materializing_transaction(entry, _evidence(entry, destination_state=state))
        assert plan.decision is RecoveryDecision.MANUAL_REVIEW


def test_recovery_rejects_source_loss(tmp_path: Path) -> None:
    entry = _candidate(tmp_path)
    with pytest.raises(PermissionError, match="preserved source"):
        reconcile_materializing_transaction(
            entry,
            _evidence(
                entry,
                destination_state=DestinationRecoveryState.MATCHES_SNAPSHOT,
                destination_verified=True,
                mutation_complete=True,
                source_preserved=False,
            ),
        )


def test_recovery_rejects_identity_mismatch(tmp_path: Path) -> None:
    entry = _candidate(tmp_path)
    with pytest.raises(ValueError, match="transaction mismatch"):
        reconcile_materializing_transaction(
            entry,
            _evidence(entry, transaction_id="wrong-transaction"),
        )


def test_recovery_does_not_accept_prepared_as_crash_candidate(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "destination"
    destination.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    state = WorkspaceStateStore(tmp_path / "snapshots").create(
        WorkspaceBinding("source", str(source), owned_or_delegated=True), engine
    )
    plan = plan_import(
        state,
        WorkspaceBinding("destination", str(destination), owned_or_delegated=True),
    )
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    entry = list(journal.replay())[-1]
    assert entry.transaction_id == transaction_id
    with pytest.raises(ValueError, match="materializing"):
        reconcile_materializing_transaction(entry, _evidence(entry))
