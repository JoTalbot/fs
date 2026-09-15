from __future__ import annotations

from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_registry import WorkspaceMode, WorkspaceRegistry
from fs_overlay.workspace_state import WorkspaceStateStore


def _binding(path: Path, workspace_id: str = "ws-1") -> WorkspaceBinding:
    return WorkspaceBinding(workspace_id, str(path), owned_or_delegated=True)


def test_workspace_state_is_scoped_to_workspace_and_content_addressed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    engine.put(b"hello")

    states = WorkspaceStateStore(tmp_path / "snapshots")
    state = states.create(_binding(workspace), engine, generation=3)

    assert state.workspace_id == "ws-1"
    assert state.snapshot.objects == tuple(engine.inventory.records)
    assert state.validate() == ()
    restored = states.get("ws-1", state.snapshot.snapshot_id)
    assert restored.snapshot == state.snapshot


def test_workspace_state_rejects_cross_workspace_snapshot(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    states = WorkspaceStateStore(tmp_path / "snapshots")
    state = states.create(_binding(workspace), engine)

    with pytest.raises(ValueError, match="snapshot_workspace_mismatch"):
        states.get("other-workspace", state.snapshot.snapshot_id)


def test_workspace_state_rejects_metadata_workspace_override(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    states = WorkspaceStateStore(tmp_path / "snapshots")

    with pytest.raises(ValueError, match="snapshot_workspace_mismatch"):
        states.create(_binding(workspace), engine, metadata={"workspace_id": "other"})


def test_registered_workspace_state_uses_registry_binding(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    registry = WorkspaceRegistry()
    registry.register(_binding(workspace), mode=WorkspaceMode.MANAGED)
    engine = LocalStorageEngine(tmp_path / "storage")
    states = WorkspaceStateStore(tmp_path / "snapshots")

    state = states.create_registered(registry, "ws-1", engine)
    assert state.snapshot.metadata == {"workspace_id": "ws-1", "workspace_mode": "managed"}


def test_workspace_state_does_not_create_missing_host_path(tmp_path: Path) -> None:
    workspace = tmp_path / "missing"
    engine = LocalStorageEngine(tmp_path / "storage")
    states = WorkspaceStateStore(tmp_path / "snapshots")

    with pytest.raises(ValueError, match="workspace_path_not_found"):
        states.create(_binding(workspace), engine)
    assert not workspace.exists()
