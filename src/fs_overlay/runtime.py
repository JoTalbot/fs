"""End-to-end execution path from declarative spec to verified transaction."""
from __future__ import annotations

import platform

from .execution_coordinator import ExecutionBoundaryPlan, plan_execution_boundaries
from .linux_executor import LinuxExecutionPolicy, LinuxNamespaceExecutor
from .model import EnvironmentSpec
from .resource_control import ResourceLease
from .supervisor import ProcessSupervisor, SupervisorPolicy
from .transaction_executor import ExecutionTransaction, TransactionExecutor
from .workspace import WorkspaceBinding


class ExecutionRuntime:
    """Connect admission, concrete Linux execution and transaction verification."""

    def __init__(
        self,
        *,
        linux_executor: LinuxNamespaceExecutor | None = None,
        transactions: TransactionExecutor | None = None,
    ) -> None:
        self.linux_executor = linux_executor or LinuxNamespaceExecutor(
            supervisor=ProcessSupervisor()
        )
        self.transactions = transactions or TransactionExecutor()

    def plan(
        self,
        spec: EnvironmentSpec,
        *,
        workspace: WorkspaceBinding | None = None,
        resource_lease: ResourceLease | None = None,
    ) -> ExecutionBoundaryPlan:
        """Return the same admission plan that execution will consume."""
        return plan_execution_boundaries(
            spec,
            workspace=workspace,
            resource_lease=resource_lease,
        )

    def execute(
        self,
        transaction_id: str,
        spec: EnvironmentSpec,
        *,
        workspace: WorkspaceBinding | None = None,
        resource_lease: ResourceLease | None = None,
        workspace_read_only: bool = True,
    ) -> ExecutionTransaction:
        """Execute an admitted spec and commit only after required verification."""
        plan = self.plan(spec, workspace=workspace, resource_lease=resource_lease)
        if not plan.admitted:
            return ExecutionTransaction(
                transaction_id,
                "rejected",
                None,
                None,
                plan.reasons or ("execution_not_admitted",),
            )
        if platform.system().lower() != "linux":
            return ExecutionTransaction(
                transaction_id,
                "rejected",
                None,
                None,
                ("linux_runtime_required",),
            )
        if not spec.command:
            return ExecutionTransaction(
                transaction_id,
                "failed",
                None,
                None,
                ("command_required",),
            )

        policy = LinuxExecutionPolicy(
            filesystem=spec.policy.filesystem,
            network=spec.policy.network,
        )
        supervisor_policy = SupervisorPolicy(
            timeout=30.0,
            restart=spec.restart,
            max_restarts=0,
        )

        def executor(**kwargs):
            return self.linux_executor.execute(
                spec.command,
                admitted=kwargs["admitted"],
                environment=spec.environment,
                policy=policy,
                workspace_path=plan.workspace.binding.host_path if plan.workspace.admitted else None,
                workspace_read_only=workspace_read_only,
                supervisor_policy=supervisor_policy,
                resource_lease=resource_lease,
                resource_budget=plan.resources.budget,
            )

        return self.transactions.execute(
            transaction_id,
            plan,
            spec.command,
            executor,
        )
