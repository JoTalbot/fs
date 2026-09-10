"""Crash/restart qualification for transactional storage publication."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fs_overlay.storage_engine import LocalStorageEngine, StorageTransaction


_CHILD_CRASH_SCRIPT = r"""
import os
import sys
from fs_overlay.storage_engine import LocalStorageEngine, StorageTransaction

root = sys.argv[1]
engine = LocalStorageEngine(root, chunk_size=4)
tx = StorageTransaction(engine)
manifest = tx.prepare(b"transactional payload")
engine.journal.append("transaction_begin", {"transaction_id": tx.transaction_id})
engine._commit_manifest(
    manifest,
    transaction_id=tx.transaction_id,
    publish_inventory=False,
)
# Simulate a process dying after durable staging/journal writes but before
# the transaction commit marker and in-memory inventory publication.
os._exit(17)
"""


def test_incomplete_transaction_is_not_published_after_process_crash(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-c", _CHILD_CRASH_SCRIPT, str(tmp_path)],
        check=False,
    )
    assert result.returncode == 17

    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    assert recovered.inventory.records == {}
    assert recovered.audit() == {
        "ok": True,
        "objects_checked": 0,
        "corrupt_objects": [],
    }


def test_durable_transaction_commit_replays_after_restart(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    tx = StorageTransaction(engine)
    manifest = tx.prepare(b"durable commit")
    committed = tx.commit()

    assert committed == (manifest,)
    assert manifest.object_id in engine.inventory.records

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
    engine._commit_manifest(
        manifest,
        transaction_id=tx.transaction_id,
        publish_inventory=False,
    )

    restarted = LocalStorageEngine(tmp_path, chunk_size=4)
    assert restarted.inventory.records == {}

    restarted.journal.append(
        "transaction_commit",
        {
            "transaction_id": tx.transaction_id,
            "object_ids": [manifest.object_id],
        },
    )
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


def test_malformed_journal_record_does_not_hide_prior_commits(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    first = engine.put(b"prior commit")
    with engine.journal.path.open("ab") as handle:
        body = b"not-json"
        handle.write(f"{len(body):016x}".encode() + body + b"\n")

    recovered = LocalStorageEngine(tmp_path, chunk_size=4)
    assert tuple(recovered.inventory.records) == (first.object_id,)
    assert recovered.get(first.object_id) == b"prior commit"


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
