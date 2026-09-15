from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_journal import TransferJournalPhase, WorkspaceTransferJournal
from fs_overlay.workspace_transfer_rollback import (
    TransferRollbackEvidence,
    validate_rollback_evidence,
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
        "destination_absent": True,
        "staging_absent": True,
        "source_preserved": True,
        "rollback_verified": True,
    }
    values.update(overrides)
    return TransferRollbackEvidence(**values)


def test_rollback_requires_complete_absence_and_verification(tmp_path: Path) -> None:
    entry = _candidate(tmp_path)
    plan = validate_rollback_evidence(entry, _evidence(entry))
    assert plan.proven is True

    for overrides in (
        {"destination_absent": False},
        {"staging_absent": False},
        {"rollback_verified": False},
    ):
        plan = validate_rollback_evidence(entry, _evidence(entry, **overrides))
        assert plan.proven is False


def test_rollback_rejects_source_loss(tmp_path: Path) -> None:
    entry = _candidate(tmp_path)
    with pytest.raises(PermissionError, match="preserved source"):
        validate_rollback_evidence(entry, _evidence(entry, source_preserved=False))


def test_rollback_rejects_identity_mismatch(tmp_path: Path) -> None:
    entry = _candidate(tmp_path)
    with pytest.raises(ValueError, match="transaction mismatch"):
        validate_rollback_evidence(entry, _evidence(entry, transaction_id="wrong"))


def test_rollback_requires_materializing_state(tmp_path: Path) -> None:
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
        validate_rollback_evidence(entry, _evidence(entry))
