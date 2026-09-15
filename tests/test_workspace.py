from pathlib import Path

from fs_overlay.workspace import WorkspaceBinding, plan_workspace


def test_workspace_requires_explicit_ownership_or_delegation(tmp_path: Path) -> None:
    binding = WorkspaceBinding("ws-1", str(tmp_path))
    plan = plan_workspace(binding)
    assert not plan.admitted
    assert "workspace_ownership_or_delegation_required" in plan.reasons


def test_workspace_admits_existing_delegated_directory(tmp_path: Path) -> None:
    binding = WorkspaceBinding("ws-1", str(tmp_path), owned_or_delegated=True)
    plan = plan_workspace(binding)
    assert plan.admitted
    assert plan.path == tmp_path
    assert plan.reasons == ()


def test_workspace_rejects_relative_path(tmp_path: Path) -> None:
    binding = WorkspaceBinding("ws-1", "relative/path", owned_or_delegated=True)
    plan = plan_workspace(binding)
    assert not plan.admitted
    assert "workspace_path_must_be_absolute" in plan.reasons


def test_workspace_rejects_symlink_root(tmp_path: Path) -> None:
    real_workspace = tmp_path / "real-workspace"
    real_workspace.mkdir()
    symlink_workspace = tmp_path / "workspace-link"
    symlink_workspace.symlink_to(real_workspace, target_is_directory=True)

    binding = WorkspaceBinding("ws-1", str(symlink_workspace), owned_or_delegated=True)
    plan = plan_workspace(binding)

    assert not plan.admitted
    assert plan.path is None
    assert plan.reasons == ("workspace_path_must_not_be_symlink",)
