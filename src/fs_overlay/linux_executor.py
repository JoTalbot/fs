"""Explicit Linux execution adapters.

Adapters execute only after admission. The workspace backend is explicit and
requires a caller-supplied admitted workspace path; it never falls back to
privileged namespace creation or silently enables a different backend.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from typing import Mapping

from .adapter import ProcessResult
from .isolation import BubblewrapWorkspaceBackend, LinuxNamespaceBackend
from .model import ResourceBudget
from .resource_control import ResourceLease
from .supervisor import ProcessSupervisor, SupervisorPolicy


@dataclass(frozen=True, slots=True)
class LinuxExecutionPolicy:
    """Explicit policy for the namespace reference executor."""

    filesystem: str = "host"
    network: str = "host"


class LinuxNamespaceExecutor:
    """Execute an already-admitted command through the selected Linux backend."""

    def __init__(
        self,
        backend: LinuxNamespaceBackend | None = None,
        workspace_backend: BubblewrapWorkspaceBackend | None = None,
        supervisor: ProcessSupervisor | None = None,
    ) -> None:
        self.backend = backend or LinuxNamespaceBackend()
        self.workspace_backend = workspace_backend or BubblewrapWorkspaceBackend()
        self.supervisor = supervisor

    def execute(
        self,
        argv: tuple[str, ...],
        *,
        admitted: bool = False,
        cwd: str | None = None,
        environment: Mapping[str, str] | None = None,
        timeout: float = 30.0,
        policy: LinuxExecutionPolicy | None = None,
        workspace_path: str | None = None,
        workspace_read_only: bool = True,
        supervisor_policy: SupervisorPolicy | None = None,
        resource_lease: ResourceLease | None = None,
        resource_budget: ResourceBudget | None = None,
    ) -> ProcessResult:
        if not admitted:
            return ProcessResult("rejected", None, "", "execution scope is not admitted")
        if not argv or not argv[0]:
            raise ValueError("argv must contain an executable")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        policy = policy or LinuxExecutionPolicy()
        backend_name = ""
        workspace_execution = False

        if policy.filesystem == "workspace-only":
            if policy.network not in {"host", "deny"}:
                return ProcessResult("rejected", None, "", "unsupported network policy")
            if workspace_path is None:
                return ProcessResult("rejected", None, "", "workspace_path_required")
            try:
                wrapped = self.workspace_backend.wrap(
                    argv,
                    workspace_path=workspace_path,
                    network=policy.network,
                    read_only=workspace_read_only,
                )
            except (RuntimeError, ValueError) as exc:
                return ProcessResult("rejected", None, "", str(exc))
            backend_name = getattr(self.workspace_backend, "name", "bubblewrap-workspace")
            workspace_execution = backend_name == "bubblewrap-workspace"
        elif policy.filesystem == "host" and policy.network == "host":
            try:
                wrapped = self.backend.wrap(argv)
            except (RuntimeError, ValueError) as exc:
                return ProcessResult("rejected", None, "", str(exc))
            backend_name = getattr(self.backend, "name", "linux-namespaces")
        else:
            return ProcessResult(
                "rejected", None, "", "requested filesystem/network policy is not enforced by this backend"
            )

        execution_evidence: tuple[str, ...] = ()
        if workspace_execution:
            execution_evidence = ("workspace-filesystem-boundary-observed",)
            if policy.network == "deny":
                execution_evidence += ("network-namespace-observed",)

        if self.supervisor is not None:
            effective_policy = supervisor_policy or SupervisorPolicy(timeout=timeout)
            return self.supervisor.execute(
                tuple(wrapped),
                admitted=True,
                cwd=None if policy.filesystem == "workspace-only" else cwd,
                environment=environment,
                policy=effective_policy,
                resource_lease=resource_lease,
                resource_budget=resource_budget,
                execution_evidence=(
                    *execution_evidence,
                    f"execution-backend:{backend_name}",
                ),
            )

        env = None
        if environment is not None:
            env = os.environ.copy()
            env.update(environment)
        try:
            completed = subprocess.run(
                list(wrapped),
                cwd=None if policy.filesystem == "workspace-only" else cwd,
                env=env,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return ProcessResult(
                "timed_out", None, exc.stdout or "", exc.stderr or "", True,
                backend=backend_name,
            )

        status = "succeeded" if completed.returncode == 0 else "failed"
        if workspace_execution and completed.returncode in self.workspace_backend.boundary_check_exit_codes:
            status = "failed"
            execution_evidence = ()

        return ProcessResult(
            status,
            completed.returncode,
            completed.stdout,
            completed.stderr,
            backend=backend_name,
            execution_evidence=execution_evidence,
        )
