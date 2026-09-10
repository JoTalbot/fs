"""Coordinate execution-boundary admission before a workload can start.

The coordinator is deliberately plan-only. It combines workspace, network,
and resource admission into one decision and never starts a process. A caller
must obtain an admitted plan before handing it to a concrete executor.
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

    reasons = list(workspace_plan.reasons) if spec.policy.filesystem == "workspace-only" else []
    if spec.policy.filesystem == "workspace-only" and workspace is not None:
        mount_plan = plan_mount_namespace(workspace)
        reasons.extend(mount_plan.reasons)
    else:
        mount_plan = MountNamespacePlan(True, True, guarantees=("filesystem-host",))

    network_plan = plan_network_namespace(requested=spec.policy.network)
    resource_plan = plan_resources(spec.policy.resources, resource_lease)
    reasons.extend(network_plan.reasons)
    reasons.extend(resource_plan.reasons)

    return ExecutionBoundaryPlan(
        admitted=not reasons,
        workspace=workspace_plan,
        network=network_plan,
        resources=resource_plan,
        reasons=tuple(reasons),
    )
