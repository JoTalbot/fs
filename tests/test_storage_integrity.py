"""Integrity and simulated durability-failure qualification for storage."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import fs_overlay.storage_engine as storage_engine
from fs_overlay.storage_engine import LocalStorageEngine, StorageTransaction


def test_corrupted_chunk_is_detected_on_read(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"integrity checked payload")
    chunk_id = manifest.chunks[0]
    chunk_path = engine.store._path(chunk_id)
    chunk_path.write_bytes(b"tampered")

    with pytest.raises(IOError, match="object integrity check failed"):
        engine.get(manifest.object_id)
    assert engine.audit() == {"ok": False, "objects_checked": 1, "corrupt_objects": [manifest.object_id]}


def test_tampered_manifest_is_rejected(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"manifest integrity")
    manifest_path = engine.store.manifests / manifest.object_id
    raw = json.loads(manifest_path.read_text())
    raw["size"] += 1
    manifest_path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False))

    with pytest.raises(ValueError, match="manifest identity verification failed"):
        engine.store.get_manifest(manifest.object_id)


def test_repeated_manifest_write_rejects_existing_corruption(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"manifest write integrity")
    manifest_path = engine.store.manifests / manifest.object_id
    raw = json.loads(manifest_path.read_text())
    raw["size"] += 1
    manifest_path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False))

    with pytest.raises(ValueError, match="manifest identity verification failed"):
        engine.store.put_manifest(manifest)


def test_manifest_object_id_mismatch_is_rejected(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"identity mismatch")
    manifest_path = engine.store.manifests / manifest.object_id
    raw = manifest_path.read_text()
    raw = raw.replace(manifest.object_id, "0" * 64, 1)
    manifest_path.write_text(raw)

    with pytest.raises(ValueError, match="manifest identity verification failed"):
        engine.store.get_manifest(manifest.object_id)


def test_manifest_rejects_boolean_numeric_fields(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"strict manifest schema")
    path = engine.store.manifests / manifest.object_id
    raw = json.loads(path.read_text())
    raw["size"] = True
    path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")))

    with pytest.raises(ValueError, match="manifest size is invalid"):
        engine.store.get_manifest(manifest.object_id)


def test_manifest_rejects_coercible_chunk_and_object_id_types(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"strict chunk types")
    path = engine.store.manifests / manifest.object_id
    raw = json.loads(path.read_text())
    raw["chunks"][0] = {"value": raw["chunks"][0]}
    path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")))

    with pytest.raises(ValueError, match="manifest chunk id is invalid"):
        engine.store.get_manifest(manifest.object_id)


def test_manifest_rejects_unexpected_fields(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"strict manifest fields")
    path = engine.store.manifests / manifest.object_id
    raw = json.loads(path.read_text())
    raw["unexpected"] = "must be rejected"
    path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")))

    with pytest.raises(ValueError, match="manifest schema is invalid"):
        engine.store.get_manifest(manifest.object_id)


def test_manifest_rejects_invalid_metadata_types(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"strict metadata types")
    path = engine.store.manifests / manifest.object_id
    raw = json.loads(path.read_text())
    raw["metadata"] = {"source": 7}
    path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")))

    with pytest.raises(ValueError, match="manifest metadata is invalid"):
        engine.store.get_manifest(manifest.object_id)


def test_manifest_rejects_duplicate_top_level_json_keys(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"duplicate manifest key")
    path = engine.store.manifests / manifest.object_id
    raw = path.read_text()
    duplicate = raw[:-1] + f',"size":{manifest.size}' + "}"
    path.write_text(duplicate)

    with pytest.raises(ValueError, match="manifest JSON is invalid"):
        engine.store.get_manifest(manifest.object_id)


def test_manifest_rejects_duplicate_nested_metadata_keys(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine.put(b"duplicate metadata key", metadata={"source": "test"})
    path = engine.store.manifests / manifest.object_id
    raw = path.read_text()
    duplicate = raw.replace('"metadata":{"source":"test"}', '"metadata":{"source":"test","source":"shadow"}')
    path.write_text(duplicate)

    with pytest.raises(ValueError, match="manifest JSON is invalid"):
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
    assert (engine.root / "journal.log").exists()
    assert (engine.store.manifests / manifest.object_id).exists()
    assert all(engine.store._path(chunk).exists() for chunk in manifest.chunks)


def test_failed_transaction_commit_marker_does_not_publish_after_restart(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    tx = StorageTransaction(engine)
    first = tx.prepare(b"staged one")
    second = tx.prepare(b"staged two")
    original_append = engine.journal.append

    def fail_commit_marker(operation: str, payload: dict[str, object]):
        if operation == "transaction_commit":
            raise OSError("simulated crash before durable transaction commit marker")
        return original_append(operation, payload)

    engine.journal.append = fail_commit_marker
    with pytest.raises(OSError, match="before durable transaction commit marker"):
        tx.commit()

    assert first.object_id not in engine.inventory.records
    assert second.object_id not in engine.inventory.records
    restored = LocalStorageEngine(tmp_path, chunk_size=4)
    assert restored.inventory.records == {}
    assert restored.recover()["objects_after"] == 0


def test_object_replace_failure_preserves_previous_committed_object(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    payload = b"durable object"
    object_id = engine.store.put(payload)
    target = engine.store._path(object_id)
    original = target.read_bytes()

    real_replace = storage_engine.os.replace

    def fail_replace(source: str, destination: str) -> None:
        if Path(destination) == target:
            raise OSError("simulated crash during object publication")
        real_replace(source, destination)

    monkeypatch.setattr(storage_engine.os, "replace", fail_replace)
    with pytest.raises(OSError, match="during object publication"):
        engine.store.put(payload + b" changed")

    assert target.read_bytes() == original
    assert engine.store.get(object_id) == payload
    assert not list(target.parent.glob(".tmp-*"))


def test_manifest_directory_fsync_failure_does_not_report_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    manifest = engine._build_manifest(b"directory durability")

    def fail_directory_sync(directory: str | Path) -> None:
        raise OSError("simulated directory fsync failure")

    monkeypatch.setattr(storage_engine, "_fsync_directory", fail_directory_sync)
    with pytest.raises(OSError, match="directory fsync failure"):
        engine.store.put_manifest(manifest)

    path = engine.store.manifests / manifest.object_id
    assert path.exists()
    assert path.read_bytes() == manifest.to_bytes()
    assert engine.store.get_manifest(manifest.object_id) == manifest
    assert not list(engine.store.manifests.glob(".tmp-*"))
