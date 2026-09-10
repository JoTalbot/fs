"""Coordinate execution-boundary admission before a workload can start.

The coordinator is deliberately plan-only. It combines workspace, mount,
network, and resource admission into one decision and never starts a process.
A caller must obtain an admitted plan before handing it to a concrete
executor. Resource leases are admission authority; concrete controllers verify
enforcement during execution.
"""
from __future__ import annotations

from dataclasses import dataclass

from .isolation import BubblewrapWorkspaceBackend
from .model import EnvironmentSpec
from .mount_namespace import MountNamespacePlan
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

    reasons: list[str]
    if spec.policy.filesystem == "workspace-only":
        workspace_backend = BubblewrapWorkspaceBackend()
        backend_plan = workspace_backend.plan(
            workspace_plan.binding.host_path if workspace_plan.admitted else None,
            network=spec.policy.network,
            read_only=workspace_plan.binding.read_only if workspace_plan.admitted else True,
        )
        reasons = list(workspace_plan.reasons)
        if not backend_plan.available:
            reasons.append(f"workspace_backend_unavailable:{backend_plan.reason}")
        mount_plan = MountNamespacePlan(
            available=backend_plan.available,
            admitted=backend_plan.available and workspace_plan.admitted,
            backend=backend_plan.backend,
            argv_prefix=backend_plan.argv_prefix,
            workspace_path=workspace_plan.binding.host_path if workspace_plan.admitted else None,
            read_only=workspace_plan.binding.read_only,
            guarantees=("workspace-filesystem-boundary",) if backend_plan.available else (),
            reasons=tuple(() if backend_plan.available else (backend_plan.reason,)),
        )
        if spec.policy.network == "deny":
            network_plan = NetworkNamespacePlan(
                available=backend_plan.available,
                admitted=backend_plan.available and workspace_plan.admitted,
                backend=backend_plan.backend,
                guarantees=("network-namespace", "network-deny-requested")
                if backend_plan.available
                else (),
                reasons=tuple(() if backend_plan.available else (backend_plan.reason,)),
            )
        else:
            network_plan = NetworkNamespacePlan(
                available=backend_plan.available,
                admitted=backend_plan.available and workspace_plan.admitted,
                backend=backend_plan.backend,
                guarantees=("host-network",),
                reasons=tuple(() if backend_plan.available else (backend_plan.reason,)),
            )
    elif spec.policy.filesystem == "host":
        mount_plan = MountNamespacePlan(True, True, guarantees=("filesystem-host",))
        reasons = []
        network_plan = plan_network_namespace(requested=spec.policy.network)
    else:
        mount_plan = MountNamespacePlan(False, False, reasons=("unsupported_filesystem_policy",))
        reasons = list(mount_plan.reasons)
        network_plan = NetworkNamespacePlan(False, False, reasons=("unsupported_filesystem_policy",))

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
