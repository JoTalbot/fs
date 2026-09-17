from __future__ import annotations

from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.storage_resilience import Snapshot
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_disaster_recovery import WorkspaceDisasterRecovery, WorkspaceRecoveryError
from fs_overlay.workspace_state import WorkspaceState, WorkspaceStateStore


def _state(tmp_path: Path) -> tuple[LocalStorageEngine, WorkspaceState]:
    source = LocalStorageEngine(tmp_path / "source", chunk_size=4)
    source.put(b"first workspace object")
    source.put(b"second workspace object")
    binding = WorkspaceBinding("workspace-1", tmp_path / "workspace", owned_or_delegated=True)
    state = WorkspaceStateStore(tmp_path / "snapshots").create(binding, source, generation=3)
    return source, state


def test_disaster_recovery_reconstructs_snapshot_into_managed_store(tmp_path: Path) -> None:
    source, state = _state(tmp_path)
    destination = tmp_path / "recovered"

    result = WorkspaceDisasterRecovery(destination).restore_from_engine(state, source)

    assert result.verified is True
    assert result.workspace_id == "workspace-1"
    assert result.snapshot_id == state.snapshot.snapshot_id
    assert result.object_count == 2
    recovered = LocalStorageEngine(destination, chunk_size=4)
    assert set(recovered.inventory.records) == set(state.snapshot.objects)
    assert recovered.audit() == {"ok": True, "objects_checked": 2, "corrupt_objects": []}


def test_disaster_recovery_rejects_tampered_snapshot_state(tmp_path: Path) -> None:
    source, state = _state(tmp_path)
    tampered_snapshot = Snapshot(
        state.snapshot.snapshot_id,
        state.snapshot.generation,
        state.snapshot.objects + ("a" * 64,),
        state.snapshot.merkle_root,
        state.snapshot.created_ns,
        state.snapshot.metadata,
    )
    tampered = WorkspaceState(state.workspace_id, tampered_snapshot)

    with pytest.raises(WorkspaceRecoveryError, match="Merkle|identity"):
        WorkspaceDisasterRecovery(tmp_path / "recovered").restore_from_engine(tampered, source)


def test_disaster_recovery_fails_when_source_manifest_is_corrupt(tmp_path: Path) -> None:
    source, state = _state(tmp_path)
    object_id = state.snapshot.objects[0]
    manifest_path = source.store.manifests / object_id
    manifest_path.write_bytes(b"corrupt")

    with pytest.raises(WorkspaceRecoveryError, match="workspace object recovery failed"):
        WorkspaceDisasterRecovery(tmp_path / "recovered").restore_from_engine(state, source)


def test_disaster_recovery_is_idempotent_for_same_snapshot(tmp_path: Path) -> None:
    source, state = _state(tmp_path)
    recovery = WorkspaceDisasterRecovery(tmp_path / "recovered")

    first = recovery.restore_from_engine(state, source)
    second = recovery.restore_from_engine(state, source)

    assert first == second
    assert LocalStorageEngine(tmp_path / "recovered", chunk_size=4).audit()["ok"] is True
