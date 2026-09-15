from pathlib import Path

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import (
    WorkspaceTransfer,
    plan_export,
    plan_import,
    plan_migration,
    plan_registered_migration,
)
from fs_overlay.workspace_registry import WorkspaceMode, WorkspaceRegistry
from fs_overlay.workspace_state import WorkspaceStateStore


def _state(tmp_path: Path):
    workspace = tmp_path / "source"
    workspace.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    engine.put(b"payload")
    store = WorkspaceStateStore(tmp_path / "snapshots")
    binding = WorkspaceBinding("source", str(workspace), owned_or_delegated=True)
    return store.create(binding, engine), binding, store


def test_export_plan_is_ready_and_preserves_source(tmp_path: Path) -> None:
    state, source, _ = _state(tmp_path)
    plan = plan_export(state, source)
    assert plan.operation is WorkspaceTransfer.EXPORT
    assert plan.ready
    assert plan.source_preserved
    assert plan.destination_path is None


def test_export_rejects_mismatched_source(tmp_path: Path) -> None:
    state, _, _ = _state(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    plan = plan_export(
        state,
        WorkspaceBinding("other", str(other), owned_or_delegated=True),
    )
    assert "source_workspace_mismatch" in plan.reasons
    assert not plan.ready


def test_import_requires_existing_managed_writable_destination(tmp_path: Path) -> None:
    state, _, _ = _state(tmp_path)
    destination = tmp_path / "destination"
    destination.mkdir()
    plan = plan_import(
        state,
        WorkspaceBinding("destination", str(destination), owned_or_delegated=True),
    )
    assert plan.operation is WorkspaceTransfer.IMPORT
    assert plan.ready
    assert plan.source_path is None
    assert plan.destination_path == destination


def test_import_rejects_read_only_destination(tmp_path: Path) -> None:
    state, _, _ = _state(tmp_path)
    destination = tmp_path / "destination"
    destination.mkdir()
    plan = plan_import(
        state,
        WorkspaceBinding("destination", str(destination), owned_or_delegated=True, read_only=True),
    )
    assert "import_destination_must_be_writable" in plan.reasons
    assert not plan.ready


def test_migration_requires_distinct_workspaces_and_preserves_source(tmp_path: Path) -> None:
    state, source, _ = _state(tmp_path)
    destination = tmp_path / "destination"
    destination.mkdir()
    plan = plan_migration(
        state,
        source,
        WorkspaceBinding("destination", str(destination), owned_or_delegated=True),
    )
    assert plan.operation is WorkspaceTransfer.MIGRATE
    assert plan.ready
    assert plan.source_preserved
    assert plan.source_path == source_path = Path(source.host_path)
