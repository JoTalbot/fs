from fs_overlay.execution_coordinator import plan_execution_boundaries
from fs_overlay.isolation import IsolationPlan
from fs_overlay.model import EnvironmentSpec, ExecutionPolicy
from fs_overlay.workspace import WorkspaceBinding


def test_default_policy_fails_closed_without_workspace(tmp_path):
    spec = EnvironmentSpec(name="demo")
    plan = plan_execution_boundaries(spec)
    assert not plan.admitted
    assert "workspace_binding_required" in plan.reasons


def test_workspace_only_requires_concrete_backend(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "fs_overlay.execution_coordinator.BubblewrapWorkspaceBackend.plan",
        lambda self, workspace_path=None, *, network="deny", read_only=True: IsolationPlan(
            "bubblewrap-workspace",
            ("/usr/bin/bwrap",),
            ("workspace-filesystem-boundary",),
            True,
        ),
    )
    spec = EnvironmentSpec(
        name="demo",
        policy=ExecutionPolicy(filesystem="workspace-only", network="deny"),
    )
    binding = WorkspaceBinding("ws-1", str(tmp_path), owned_or_delegated=True)
    plan = plan_execution_boundaries(spec, workspace=binding)
    assert plan.admitted
    assert plan.workspace.admitted
    assert "workspace-filesystem-boundary" in plan.mount.guarantees
    assert "network-namespace" in plan.network.guarantees
    assert "workspace_isolation_not_enforced" not in plan.reasons


def test_host_policy_does_not_require_workspace(tmp_path):
    spec = EnvironmentSpec(
        name="demo",
        policy=ExecutionPolicy(filesystem="host", network="host"),
    )
    plan = plan_execution_boundaries(spec)
    assert plan.workspace.admitted is False
    assert plan.network.admitted
