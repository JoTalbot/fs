from fs_overlay.execution_coordinator import ExecutionBoundaryPlan
from fs_overlay.verification_requirements import required_verification_checks
from fs_overlay.workspace import WorkspaceBinding, WorkspacePlan
from fs_overlay.mount_namespace import MountNamespacePlan
from fs_overlay.network_namespace import NetworkNamespacePlan
from fs_overlay.resource_control import ResourcePlan
from fs_overlay.model import ResourceBudget


def _plan(mount_guarantees=(), network_guarantees=()):
    return ExecutionBoundaryPlan(
        admitted=True,
        workspace=WorkspacePlan(WorkspaceBinding("w", "/tmp"), True, "/tmp"),
        mount=MountNamespacePlan(True, True, guarantees=mount_guarantees),
        network=NetworkNamespacePlan(True, True, guarantees=network_guarantees),
        resources=ResourcePlan(ResourceBudget(), None, True),
    )


def test_isolation_guarantees_require_namespace_checks():
    checks = required_verification_checks(
        _plan(("mount-namespace", "pid-namespace"), ("network-namespace",))
    )
    assert [check.check_id for check in checks] == [
        "namespace:mount",
        "namespace:pid",
        "namespace:net",
    ]


def test_workspace_boundary_requires_exact_execution_evidence():
    checks = required_verification_checks(_plan(("workspace-filesystem-boundary",)))
    assert [check.check_id for check in checks] == ["workspace:boundary"]


def test_unmapped_guarantees_do_not_create_fake_evidence_requirements():
    checks = required_verification_checks(_plan(("workspace-binding-admitted",), ("host-network",)))
    assert checks == ()
