"""Qualification of transaction publication when the durable commit marker fails."""
from __future__ import annotations

from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine, StorageTransaction


def test_commit_marker_append_failure_does_not_publish_staged_objects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    tx = StorageTransaction(engine)
    manifest = tx.prepare(b"commit marker failure")
    original_append = engine.journal.append

    def fail_commit_marker(operation: str, payload: dict[str, object]) -> dict[str, object]:
        if operation == "transaction_commit":
            raise OSError("injected transaction commit marker failure")
        return original_append(operation, payload)

    monkeypatch.setattr(engine.journal, "append", fail_commit_marker)
    with pytest.raises(OSError, match="commit marker failure"):
        tx.commit()

    assert engine.inventory.records == {}
    restarted = LocalStorageEngine(tmp_path, chunk_size=4)
    assert restarted.inventory.records == {}
    assert restarted.get(manifest.object_id) == b"commit marker failure"
    assert restarted.audit() == {
        "ok": True,
        "objects_checked": 0,
        "corrupt_objects": [],
    }
