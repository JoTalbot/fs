from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_materializer import (
    MaterializationRejected,
    WorkspaceMaterializer,
    validate_materialization_context,
)
from fs_overlay.workspace_migration import plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_authority import (
    TransferAuthorityScope,
    grant_transfer_authority,
)
from fs_overlay.workspace_transfer_journal import (
    TransferJournalPhase,
    WorkspaceTransferJournal,
)


def _context(tmp_path: Path):
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
    authority = grant_transfer_authority(
        plan,
        transaction_id=transaction_id,
        scope=TransferAuthorityScope.MATERIALIZE,
        approved=True,
    )
    return plan, journal, authority, destination


def test_materializer_requires_exact_authority_and_journal_binding(tmp_path: Path) -> None:
    plan, journal, authority, _ = _context(tmp_path)
    context = validate_materialization_context(authority, plan, journal)
    assert context.transaction_id == authority.transaction_id


def test_materializer_prepare_only_advances_journal(tmp_path: Path) -> None:
    plan, journal, authority, destination = _context(tmp_path)
    before = sorted(destination.iterdir())
    WorkspaceMaterializer(journal).prepare(
        validate_materialization_context(authority, plan, journal)
    )
    assert sorted(destination.iterdir()) == before
    assert [entry.phase for entry in journal.replay()] == [
        TransferJournalPhase.PREPARED,
        TransferJournalPhase.MATERIALIZING,
    ]


def test_materializer_rejects_terminal_transaction(tmp_path: Path) -> None:
    plan, journal, authority, _ = _context(tmp_path)
    journal.mark(authority.transaction_id, plan, TransferJournalPhase.ABORTED)
    with pytest.raises(MaterializationRejected, match="already terminal"):
        validate_materialization_context(authority, plan, journal)


def test_materializer_rejects_mismatched_authority(tmp_path: Path) -> None:
    plan, journal, authority, _ = _context(tmp_path)
    mismatched = authority.__class__(
        transaction_id=authority.transaction_id,
        snapshot_id="different-snapshot",
        source_workspace_id=authority.source_workspace_id,
        destination_workspace_id=authority.destination_workspace_id,
        scope=authority.scope,
        source_preserved=authority.source_preserved,
    )
    with pytest.raises(MaterializationRejected, match="snapshot"):
        validate_materialization_context(mismatched, plan, journal)


def test_materializer_commit_is_explicitly_blocked(tmp_path: Path) -> None:
    plan, journal, authority, _ = _context(tmp_path)
    materializer = WorkspaceMaterializer(journal)
    context = validate_materialization_context(authority, plan, journal)
    with pytest.raises(NotImplementedError, match="crash-safe executor"):
        materializer.commit(context)


def test_materializer_abort_is_journal_only(tmp_path: Path) -> None:
    plan, journal, authority, destination = _context(tmp_path)
    materializer = WorkspaceMaterializer(journal)
    context = validate_materialization_context(authority, plan, journal)
    materializer.abort(context)
    assert not list(destination.iterdir())
    assert list(journal.replay())[-1].phase is TransferJournalPhase.ABORTED
