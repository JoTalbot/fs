from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_journal import (
    TransferJournalCorruption,
    WorkspaceTransferJournal,
)


def _plan(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "destination"
    destination.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    engine.put(b"payload")
    state = WorkspaceStateStore(tmp_path / "snapshots").create(
        WorkspaceBinding("source", str(source), owned_or_delegated=True), engine
    )
    return plan_import(
        state,
        WorkspaceBinding("destination", str(destination), owned_or_delegated=True),
    )


def test_journal_requires_ready_plan(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    state = WorkspaceStateStore(tmp_path / "snapshots").create(
        WorkspaceBinding("source", str(source), owned_or_delegated=True), engine
    )
    plan = plan_import(state, WorkspaceBinding("destination", "/missing", owned_or_delegated=True))
    with pytest.raises(ValueError, match="not ready"):
        WorkspaceTransferJournal(tmp_path / "journal.log").begin(plan)


def test_journal_round_trip_and_explicit_phases(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    journal.mark(transaction_id, plan, "materializing")
    journal.mark(transaction_id, plan, "committed")

    entries = list(journal.replay())
    assert [entry.phase for entry in entries] == ["prepared", "materializing", "committed"]
    assert all(entry.transaction_id == transaction_id for entry in entries)
    assert all(entry.source_workspace_id == "source" for entry in entries)


def test_journal_ignores_only_incomplete_eof_tail(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "journal.log"
    journal = WorkspaceTransferJournal(path)
    journal.begin(plan)
    with path.open("ab") as handle:
        handle.write(b'{"version":1,"phase":"incomplete"')
    assert len(list(journal.replay())) == 1


def test_journal_rejects_malformed_non_tail_record(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "journal.log"
    journal = WorkspaceTransferJournal(path)
    journal.begin(plan)
    with path.open("ab") as handle:
        handle.write(b'{bad\n')
        handle.write(b'{"version":1}\n')
    with pytest.raises(TransferJournalCorruption):
        list(journal.replay())
