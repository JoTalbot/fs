"""Integrity qualification for content-addressed storage and manifests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine, StorageTransaction


def test_corrupted_chunk_is_detected_on_read(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"integrity checked payload")
    chunk_id = manifest.chunks[0]
    chunk_path = engine.store._path(chunk_id)
    chunk_path.write_bytes(b"tampered")

    with pytest.raises(IOError, match="object integrity check failed"):
        engine.get(manifest.object_id)
    assert engine.audit() == {
        "ok": False,
        "objects_checked": 1,
        "corrupt_objects": [manifest.object_id],
    }


def test_tampered_manifest_is_rejected(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"manifest integrity")
    manifest_path = engine.store.manifests / manifest.object_id
    raw = json.loads(manifest_path.read_text())
    raw["size"] += 1
    manifest_path.write_text(
        json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    )

    with pytest.raises(ValueError, match="manifest identity verification failed"):
        engine.store.get_manifest(manifest.object_id)


def test_manifest_object_id_mismatch_is_rejected(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"identity mismatch")
    manifest_path = engine.store.manifests / manifest.object_id
    raw = manifest_path.read_text()
    raw = raw.replace(manifest.object_id, "0" * 64, 1)
    manifest_path.write_text(raw)

    with pytest.raises(ValueError, match="manifest identity verification failed"):
        engine.store.get_manifest(manifest.object_id)


def test_repeated_content_addressed_write_is_idempotent(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    payload = b"same content-addressed object"
    first = engine.put(payload)
    object_path = engine.store._path(first.chunks[0])
    original = object_path.read_bytes()

    second = engine.put(payload)

    assert second == first
    assert object_path.read_bytes() == original
    assert tuple(engine.inventory.records) == (first.object_id,)


def test_rollback_leaves_no_published_inventory_record(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    tx = StorageTransaction(engine)
    manifest = tx.prepare(b"rollback orphan candidate")
    tx.rollback()

    assert manifest.object_id not in engine.inventory.records
    assert not (engine.root / "inventory.log").exists()
    assert (engine.store.manifests / manifest.object_id).exists()
    assert all(engine.store._path(chunk).exists() for chunk in manifest.chunks)
