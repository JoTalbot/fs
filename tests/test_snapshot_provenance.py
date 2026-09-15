"""Cross-object substitution regressions for content-addressed state."""
from __future__ import annotations

from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.storage_resilience import SnapshotStore


def test_valid_alternate_manifest_cannot_replace_referenced_manifest(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path / "storage", chunk_size=4)
    first = engine.put(b"first payload")
    second = engine.put(b"second payload")

    target = engine.store.manifests / first.object_id
    alternate = engine.store.manifests / second.object_id
    target.write_bytes(alternate.read_bytes())

    with pytest.raises(ValueError, match="manifest identity verification failed"):
        engine.store.get_manifest(first.object_id)


def test_valid_alternate_snapshot_cannot_replace_referenced_snapshot(tmp_path: Path) -> None:
    store = SnapshotStore(tmp_path / "snapshots")
    first = store.create(("a" * 64,), generation=1, metadata={"workspace_id": "ws-1"})
    second = store.create(("b" * 64,), generation=2, metadata={"workspace_id": "ws-2"})

    target = tmp_path / "snapshots" / first.snapshot_id
    alternate = tmp_path / "snapshots" / second.snapshot_id
    target.write_bytes(alternate.read_bytes())

    with pytest.raises(ValueError, match="snapshot identity verification failed"):
        store.get(first.snapshot_id)
