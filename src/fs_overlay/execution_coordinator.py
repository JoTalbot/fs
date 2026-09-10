"""Coordinate execution-boundary admission before a workload can start.

The coordinator is deliberately plan-only. It combines workspace, mount,
network, and resource admission into one decision and never starts a process.
A caller must obtain an admitted plan before handing it to a concrete
executor.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import EnvironmentSpec
from .mount_namespace import MountNamespacePlan, plan_mount_namespace
from .network_namespace import NetworkNamespacePlan, plan_network_namespace
from .resource_control import ResourceLease, ResourcePlan, plan_resources
from .workspace import WorkspaceBinding, WorkspacePlan, plan_workspace


@dataclass(frozen=True, slots=True)
class ExecutionBoundaryPlan:
    admitted: bool
    workspace: WorkspacePlan
    mount: MountNamespacePlan
    network: NetworkNamespacePlan
    resources: ResourcePlan
    reasons: tuple[str, ...] = ()


def plan_execution_boundaries(
    spec: EnvironmentSpec,
    *,
    workspace: WorkspaceBinding | None = None,
    resource_lease: ResourceLease | None = None,
) -> ExecutionBoundaryPlan:
    """Build one fail-closed admission decision for all requested boundaries."""
    if workspace is None:
        workspace_plan = WorkspacePlan(
            WorkspaceBinding("", ""), False, None, ("workspace_binding_required",)
        )
    else:
        workspace_plan = plan_workspace(workspace)

    if spec.policy.filesystem == "workspace-only":
        mount_plan = plan_mount_namespace(workspace or WorkspaceBinding("", ""))
        reasons = list(mount_plan.reasons)
        if workspace_plan.reasons:
            reasons.extend(r for r in workspace_plan.reasons if r not in reasons)
        # A mount namespace by itself does not establish a workspace-only
        # filesystem. Until a backend performs and verifies the actual
        # workspace binding, admission must fail closed.
        if workspace_plan.admitted and "workspace_isolation_not_enforced" not in reasons:
            reasons.append("workspace_isolation_not_enforced")
    elif spec.policy.filesystem == "host":
        mount_plan = MountNamespacePlan(True, True, guarantees=("filesystem-host",))
        reasons = []
    else:
        mount_plan = MountNamespacePlan(False, False, reasons=("unsupported_filesystem_policy",))
        reasons = list(mount_plan.reasons)

    network_plan = plan_network_namespace(requested=spec.policy.network)
    resource_plan = plan_resources(spec.policy.resources, resource_lease)
    reasons.extend(network_plan.reasons)
    reasons.extend(resource_plan.reasons)

    return ExecutionBoundaryPlan(
        admitted=not reasons,
        workspace=workspace_plan,
        mount=mount_plan,
        network=network_plan,
        resources=resource_plan,
        reasons=tuple(reasons),
    )
