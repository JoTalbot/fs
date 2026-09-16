"""Crash/restart qualification for transactional storage publication."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from fs_overlay.storage_engine import AppendJournal, JournalCorruption, LocalStorageEngine, StorageTransaction


_CHILD_CRASH_SCRIPT = r"""
import os
import sys
from fs_overlay.storage_engine import LocalStorageEngine, StorageTransaction
root = sys.argv[1]
engine = LocalStorageEngine(root, chunk_size=4)
tx = StorageTransaction(engine)
manifest = tx.prepare(b"transactional payload")
engine.journal.append("transaction_begin", {"transaction_id": tx.transaction_id})
engine._commit_manifest(manifest, transaction_id=tx.transaction_id, publish_inventory=False)
os._exit(17)
"""

_CHILD_PARTIAL_MULTI_OBJECT_CRASH_SCRIPT = r"""
import os
import sys
from fs_overlay.storage_engine import LocalStorageEngine, StorageTransaction
root = sys.argv[1]
engine = LocalStorageEngine(root, chunk_size=4)
tx = StorageTransaction(engine)
first = tx.prepare(b"first partial object")
second = tx.prepare(b"second partial object")
engine.journal.append("transaction_begin", {"transaction_id": tx.transaction_id})
engine._commit_manifest(first, transaction_id=tx.transaction_id, publish_inventory=False)
os._exit(21)
"""

_CHILD_POST_COMMIT_CRASH_SCRIPT = r"""
import os
import sys
from fs_overlay.storage_engine import LocalStorageEngine, StorageTransaction
root = sys.argv[1]
engine = LocalStorageEngine(root, chunk_size=4)
tx = StorageTransaction(engine)
manifest = tx.prepare(b"post-commit crash payload")
engine.journal.append("transaction_begin", {"transaction_id": tx.transaction_id})
engine._commit_manifest(manifest, transaction_id=tx.transaction_id, publish_inventory=False)
engine.journal.append("transaction_commit", {
    "transaction_id": tx.transaction_id,
    "object_ids": [manifest.object_id],
})
os._exit(19)
"""


def test_incomplete_transaction_is_not_published_after_process_crash(tmp_path: Path) -> None:
    result = subprocess.run([sys.executable, "-c", _CHILD_CRASH_SCRIPT, str(tmp_path)], check=False)
    assert result.returncode == 17
    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    assert recovered.inventory.records == {}
    assert recovered.audit() == {"ok": True, "objects_checked": 0, "corrupt_objects": []}


def test_partial_multi_object_transaction_is_not_published_after_crash(tmp_path: Path) -> None:
    result = subprocess.run([sys.executable, "-c", _CHILD_PARTIAL_MULTI_OBJECT_CRASH_SCRIPT, str(tmp_path)], check=False)
    assert result.returncode == 21
    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    assert recovered.inventory.records == {}
    assert recovered.audit() == {"ok": True, "objects_checked": 0, "corrupt_objects": []}


def test_committed_transaction_is_recovered_after_process_crash_before_memory_publish(tmp_path: Path) -> None:
    result = subprocess.run([sys.executable, "-c", _CHILD_POST_COMMIT_CRASH_SCRIPT, str(tmp_path)], check=False)
    assert result.returncode == 19
    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    assert len(recovered.inventory.records) == 1
    manifest = next(iter(recovered.inventory.records.values()))
    assert recovered.get(manifest.object_id) == b"post-commit crash payload"
    assert recovered.audit()["ok"] is True


def test_durable_transaction_commit_replays_after_restart(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    tx = StorageTransaction(engine)
    manifest = tx.prepare(b"durable commit")
    assert tx.commit() == (manifest,)
    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    assert tuple(recovered.inventory.records) == (manifest.object_id,)
    assert recovered.get(manifest.object_id) == b"durable commit"
    assert recovered.audit()["ok"] is True


def test_single_object_commit_replays_after_restart(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"ordinary durable object")
    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    assert tuple(recovered.inventory.records) == (manifest.object_id,)
    assert recovered.get(manifest.object_id) == b"ordinary durable object"


def test_rollback_remains_unpublished_after_restart(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    tx = StorageTransaction(engine)
    manifest = tx.prepare(b"rolled back")
    tx.rollback()
    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    assert manifest.object_id not in recovered.inventory.records
    assert recovered.inventory.records == {}


def test_recovery_can_complete_a_transaction_after_restart(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    tx = StorageTransaction(engine)
    manifest = tx.prepare(b"recoverable")
    engine.journal.append("transaction_begin", {"transaction_id": tx.transaction_id})
    engine._commit_manifest(manifest, transaction_id=tx.transaction_id, publish_inventory=False)
    restarted = LocalStorageEngine(tmp_path, chunk_size=4)
    assert restarted.inventory.records == {}
    restarted.journal.append("transaction_commit", {"transaction_id": tx.transaction_id, "object_ids": [manifest.object_id]})
    restarted.recover()
    assert tuple(restarted.inventory.records) == (manifest.object_id,)
    assert restarted.get(manifest.object_id) == b"recoverable"


def test_truncated_journal_tail_does_not_corrupt_prior_commits(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    first = engine.put(b"durable before tail")
    with engine.journal.path.open("ab") as handle:
        handle.write(b"0000000000000100{\"truncated\":true")
    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    assert tuple(recovered.inventory.records) == (first.object_id,)
    assert recovered.get(first.object_id) == b"durable before tail"
    assert recovered.audit()["ok"] is True


def test_truncated_journal_length_tail_is_ignored(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path)
    first = engine.put(b"before truncated header")
    with engine.journal.path.open("ab") as handle:
        handle.write(b"00000000")
    recovered = LocalStorageEngine(tmp_path)
    assert tuple(recovered.inventory.records) == (first.object_id,)


def test_truncated_journal_payload_tail_is_ignored(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path)
    first = engine.put(b"before truncated payload")
    with engine.journal.path.open("ab") as handle:
        handle.write(b"0000000000000010short")
    recovered = LocalStorageEngine(tmp_path)
    assert tuple(recovered.inventory.records) == (first.object_id,)


def test_malformed_complete_journal_record_at_tail_fails_closed(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path)
    engine.put(b"prior commit")
    with engine.journal.path.open("ab") as handle:
        body = b"not-json"
        handle.write(f"{len(body):016x}".encode() + body + b"\n")
    with pytest.raises(JournalCorruption, match="malformed JSON"):
        LocalStorageEngine(tmp_path)


def test_malformed_complete_journal_record_in_middle_fails_closed(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path)
    engine.put(b"prior commit")
    prefix = engine.journal.path.read_bytes()
    engine.put(b"later commit")
    suffix = engine.journal.path.read_bytes()[len(prefix):]
    body = b"not-json"
    malformed = f"{len(body):016x}".encode() + body + b"\n"
    engine.journal.path.write_bytes(prefix + malformed + suffix)
    with pytest.raises(JournalCorruption):
        list(AppendJournal(engine.journal.path).replay())
    with pytest.raises(JournalCorruption):
        LocalStorageEngine(tmp_path)


def test_recovery_replay_is_idempotent(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    first = engine.put(b"idempotent recovery")
    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    before = dict(recovered.inventory.records)
    assert recovered.recover()["objects_after"] == 1
    assert recovered.recover()["objects_after"] == 1
    assert recovered.inventory.records == before
    assert recovered.get(first.object_id) == b"idempotent recovery"


def test_multiple_transactions_replay_in_commit_order(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    first_tx = StorageTransaction(engine)
    first = first_tx.prepare(b"first transaction")
    first_tx.commit()
    second_tx = StorageTransaction(engine)
    second = second_tx.prepare(b"second transaction")
    second_tx.commit()
    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    assert tuple(recovered.inventory.records) == (first.object_id, second.object_id)
    assert recovered.get(first.object_id) == b"first transaction"
    assert recovered.get(second.object_id) == b"second transaction"
    assert recovered.audit()["ok"] is True


def _append_record(path: Path, record: dict[str, object]) -> None:
    body = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    with path.open("ab") as handle:
        handle.write(f"{len(body):016x}".encode() + body + b"\n")


def test_journal_rejects_boolean_version_even_when_json_is_complete(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path)
    engine.put(b"prior commit")
    _append_record(engine.journal.path, {
        "version": True,
        "operation": "delete",
        "payload": {"object_id": "0" * 64},
    })
    with pytest.raises(JournalCorruption, match="version"):
        list(AppendJournal(engine.journal.path).replay())


def test_journal_rejects_unknown_operation_before_inventory_mutation(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path)
    engine.put(b"prior commit")
    _append_record(engine.journal.path, {
        "version": 1,
        "operation": "grant",
        "payload": {"object_id": "0" * 64},
    })
    with pytest.raises(JournalCorruption, match="operation"):
        LocalStorageEngine(tmp_path)


def test_journal_rejects_coercible_commit_types(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path)
    engine.put(b"prior commit")
    _append_record(engine.journal.path, {
        "version": 1,
        "operation": "commit",
        "payload": {
            "object_id": 123,
            "size": "7",
            "manifest_path": "123",
        },
    })
    with pytest.raises(JournalCorruption, match="object_id"):
        LocalStorageEngine(tmp_path)


def test_journal_rejects_extra_commit_field(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path)
    engine.put(b"prior commit")
    _append_record(engine.journal.path, {
        "version": 1,
        "operation": "commit",
        "payload": {
            "object_id": "0" * 64,
            "size": 7,
            "manifest_path": "0" * 64,
            "unexpected": "value",
        },
    })
    with pytest.raises(JournalCorruption, match="commit payload schema"):
        LocalStorageEngine(tmp_path)


def test_journal_rejects_boolean_size(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path)
    engine.put(b"prior commit")
    _append_record(engine.journal.path, {
        "version": 1,
        "operation": "commit",
        "payload": {
            "object_id": "0" * 64,
            "size": True,
            "manifest_path": "0" * 64,
        },
    })
    with pytest.raises(JournalCorruption, match="size"):
        LocalStorageEngine(tmp_path)


def test_journal_rejects_malformed_transaction_commit_payload(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path)
    engine.put(b"prior commit")
    _append_record(engine.journal.path, {
        "version": 1,
        "operation": "transaction_commit",
        "payload": {"transaction_id": "tx", "object_ids": ["not-an-object-id"]},
    })
    with pytest.raises(JournalCorruption, match="object_id"):
        LocalStorageEngine(tmp_path)
