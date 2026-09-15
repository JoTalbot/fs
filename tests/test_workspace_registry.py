from pathlib import Path

import pytest

from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_registry import WorkspaceHealth, WorkspaceMode, WorkspaceRegistry


def test_registry_registers_observed_workspace(tmp_path: Path) -> None:
    registry = WorkspaceRegistry()
    record = registry.register(
        WorkspaceBinding("ws-1", str(tmp_path), owned_or_delegated=True),
        mode=WorkspaceMode.OBSERVED,
    )
    assert record.mode is WorkspaceMode.OBSERVED
    assert record.health is WorkspaceHealth.HEALTHY
    assert record.path == tmp_path


def test_registry_rejects_unowned_managed_workspace(tmp_path: Path) -> None:
    registry = WorkspaceRegistry()
    with pytest.raises(ValueError, match="managed_workspace_requires_ownership_or_delegation"):
        registry.register(WorkspaceBinding("ws-1", str(tmp_path)), mode=WorkspaceMode.MANAGED)


def test_registry_reports_missing_workspace_and_refreshes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    registry = WorkspaceRegistry()
    record = registry.register(
        WorkspaceBinding("ws-1", str(workspace), owned_or_delegated=True),
        mode=WorkspaceMode.MANAGED,
    )
    assert record.health is WorkspaceHealth.NOT_FOUND

    workspace.mkdir()
    refreshed = registry.refresh_health("ws-1")
    assert refreshed.health is WorkspaceHealth.HEALTHY
    assert refreshed.path == workspace


def test_registry_rejects_duplicate_id(tmp_path: Path) -> None:
    registry = WorkspaceRegistry()
    binding = WorkspaceBinding("ws-1", str(tmp_path), owned_or_delegated=True)
    registry.register(binding, mode=WorkspaceMode.OBSERVED)
    with pytest.raises(ValueError, match="workspace_id_already_registered"):
        registry.register(binding, mode=WorkspaceMode.OBSERVED)


def test_registry_fails_closed_for_symlink_root(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)

    registry = WorkspaceRegistry()
    record = registry.register(
        WorkspaceBinding("ws-1", str(link), owned_or_delegated=True),
        mode=WorkspaceMode.OBSERVED,
    )
    assert record.health is WorkspaceHealth.INVALID
    assert record.path is None
