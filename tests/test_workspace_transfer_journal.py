from dataclasses import replace
from pathlib import Path
import hashlib
import json

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_journal import (
    TransferJournalCorruption,
    TransferJournalPhase,
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
    journal.mark(transaction_id, plan, TransferJournalPhase.MATERIALIZING)
    journal.mark(transaction_id, plan, TransferJournalPhase.COMMITTED)

    entries = list(journal.replay())
    assert [entry.phase for entry in entries] == [
        TransferJournalPhase.PREPARED,
        TransferJournalPhase.MATERIALIZING,
        TransferJournalPhase.COMMITTED,
    ]
    assert all(entry.transaction_id == transaction_id for entry in entries)
    assert all(entry.source_workspace_id == "source" for entry in entries)
    assert journal.recovery_candidates() == ()


def test_journal_hash_chain_is_durable_and_reopen_safe(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "journal.log"
    journal = WorkspaceTransferJournal(path)
    transaction_id = journal.begin(plan)
    journal.mark(transaction_id, plan, TransferJournalPhase.MATERIALIZING)
    first = list(journal.replay())
    assert len(first) == 2
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert records[0]["previous_digest"] is None
    assert records[1]["previous_digest"] == records[0]["event_digest"]
    assert all(len(record["event_digest"]) == 64 for record in records)
    reopened = WorkspaceTransferJournal(path)
    assert list(reopened.replay()) == first
    assert reopened.recovery_candidates()[0].transaction_id == transaction_id


def test_journal_rejects_tampered_event_even_when_json_remains_valid(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "journal.log"
    journal = WorkspaceTransferJournal(path)
    journal.begin(plan)
    raw = path.read_text().replace('"phase":"prepared"', '"phase":"aborted"')
    path.write_text(raw)
    with pytest.raises(TransferJournalCorruption, match="digest mismatch"):
        list(journal.replay())


def test_journal_rejects_broken_chain_even_with_repaired_digest(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "journal.log"
    journal = WorkspaceTransferJournal(path)
    transaction_id = journal.begin(plan)
    journal.mark(transaction_id, plan, TransferJournalPhase.MATERIALIZING)
    lines = path.read_text().splitlines()
    record = json.loads(lines[1])
    record["previous_digest"] = "0" * 64
    record["event_digest"] = None
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    record["event_digest"] = hashlib.sha256(encoded).hexdigest()
    lines[1] = json.dumps(record, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(TransferJournalCorruption, match="hash chain"):
        list(journal.replay())


def test_journal_rejects_invalid_transition_and_terminal_advance(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    with pytest.raises(ValueError, match="invalid transfer journal transition"):
        journal.mark(transaction_id, plan, TransferJournalPhase.COMMITTED)

    journal.mark(transaction_id, plan, TransferJournalPhase.ABORTED)
    with pytest.raises(ValueError, match="invalid transfer journal transition"):
        journal.mark(transaction_id, plan, TransferJournalPhase.MATERIALIZING)


def test_journal_rejects_unknown_transaction(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    with pytest.raises(ValueError, match="unknown transfer transaction"):
        journal.mark("missing", plan, TransferJournalPhase.MATERIALIZING)


def test_journal_rejects_identity_change(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    conflicting = replace(plan, destination_workspace_id="other-destination")
    with pytest.raises(ValueError, match="transaction identity mismatch"):
        journal.mark(transaction_id, conflicting, TransferJournalPhase.MATERIALIZING)


def test_journal_reopen_can_continue_valid_transaction(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "journal.log"
    transaction_id = WorkspaceTransferJournal(path).begin(plan)
    reopened = WorkspaceTransferJournal(path)
    reopened.mark(transaction_id, plan, TransferJournalPhase.MATERIALIZING)
    assert len(reopened.recovery_candidates()) == 1
    reopened.mark(transaction_id, plan, TransferJournalPhase.COMMITTED)
    assert reopened.recovery_candidates() == ()


def test_journal_replay_rejects_unsupported_legacy_record(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "journal.log"
    journal = WorkspaceTransferJournal(path)
    journal.begin(plan)
    raw = path.read_text().replace('"version":2', '"version":1')
    path.write_text(raw)
    with pytest.raises(TransferJournalCorruption, match="unsupported journal version"):
        list(journal.replay())


def test_journal_ignores_only_incomplete_eof_tail(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "journal.log"
    journal = WorkspaceTransferJournal(path)
    journal.begin(plan)
    with path.open("ab") as handle:
        handle.write(b'{"version":2,"phase":"incomplete"')
    assert len(list(journal.replay())) == 1


def test_journal_rejects_malformed_non_tail_record(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "journal.log"
    journal = WorkspaceTransferJournal(path)
    journal.begin(plan)
    with path.open("ab") as handle:
        handle.write(b'{bad\n')
        handle.write(b'{"version":2}\n')
    with pytest.raises(TransferJournalCorruption):
        list(journal.replay())
