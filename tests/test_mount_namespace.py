from fs_overlay.mount_namespace import plan_mount_namespace
from fs_overlay.workspace import WorkspaceBinding


def test_mount_namespace_requires_explicit_workspace_admission(tmp_path):
    binding = WorkspaceBinding("ws-1", str(tmp_path))
    plan = plan_mount_namespace(binding)
    assert not plan.admitted
    assert "workspace_ownership_or_delegation_required" in plan.reasons


def test_mount_namespace_plan_is_non_mutating(tmp_path):
    binding = WorkspaceBinding("ws-1", str(tmp_path), owned_or_delegated=True)
    before = sorted(p.name for p in tmp_path.iterdir())
    plan = plan_mount_namespace(binding)
    after = sorted(p.name for p in tmp_path.iterdir())
    assert before == after
    if plan.admitted:
        assert "mount-namespace" in plan.guarantees
        assert plan.workspace_path == str(tmp_path)
