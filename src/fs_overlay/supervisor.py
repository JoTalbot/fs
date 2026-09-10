"""Bounded process supervision for admitted FS workloads.

The supervisor owns a child process lifetime, timeout, restart budget, and
platform-native resource attachment. It never uses a shell and never expands
authority when a resource controller is unavailable.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import signal
import subprocess
from typing import Mapping, Protocol

from .adapter import ProcessResult
from .cgroup_v2 import LinuxCgroupV2Backend
from .model import ResourceBudget
from .resource_control import ResourceLease
from .windows_job import WindowsJobObjectBackend


class ResourceController(Protocol):
    def apply(self, pid: int, lease: ResourceLease | None, budget: ResourceBudget) -> object: ...
    def release(self, pid: int | None) -> None: ...


@dataclass(frozen=True, slots=True)
class SupervisorPolicy:
    timeout: float = 30.0
    restart: str = "never"
    max_restarts: int = 0

    def validate(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.timeout <= 0:
            reasons.append("timeout_must_be_positive")
        if self.restart not in {"never", "on-failure"}:
            reasons.append("unsupported_restart_policy")
        if self.max_restarts < 0:
            reasons.append("max_restarts_must_be_non_negative")
        if self.restart == "never" and self.max_restarts:
            reasons.append("max_restarts_requires_on_failure")
        return tuple(reasons)


def _default_resource_backend() -> ResourceController:
    return WindowsJobObjectBackend() if os.name == "nt" else LinuxCgroupV2Backend()


class ProcessSupervisor:
    """Run an admitted argv under a bounded lifecycle policy."""

    def __init__(self, resource_backend: ResourceController | None = None) -> None:
        self.resource_backend = resource_backend or _default_resource_backend()

    def _release(self, pid: int | None) -> None:
        release = getattr(self.resource_backend, "release", None)
        if release is not None:
            release(pid)

    def _terminate(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGTERM)
                return
            except (OSError, ProcessLookupError):
                pass
        process.terminate()

    def _kill(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
                return
            except (OSError, ProcessLookupError):
                pass
        process.kill()

    def _once(self, argv: tuple[str, ...], *, cwd: str | None,
              environment: Mapping[str, str] | None, policy: SupervisorPolicy,
              resource_lease: ResourceLease | None, resource_budget: ResourceBudget,
              execution_evidence: tuple[str, ...] = ()) -> ProcessResult:
        env = os.environ.copy()
        if environment is not None:
            env.update(environment)
        try:
            process = subprocess.Popen(
                list(argv), cwd=cwd, env=env, shell=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                start_new_session=(os.name == "posix"),
            )
        except OSError as exc:
            return ProcessResult("failed", None, "", f"spawn_failed:{type(exc).__name__}")

        resource_requested = any(value is not None for value in (
            resource_budget.cpu_millis, resource_budget.memory_bytes,
            resource_budget.disk_bytes, resource_budget.pids,
        ))
        resource_evidence = ()
        resource_lease_id = None
        if resource_requested:
            resource_result = self.resource_backend.apply(process.pid, resource_lease, resource_budget)
            if not getattr(resource_result, "verified", False):
                self._terminate(process)
                try:
                    process.communicate(timeout=2.0)
                except subprocess.TimeoutExpired:
                    self._kill(process)
                    process.communicate()
                self._release(process.pid)
                reason = getattr(resource_result, "reasons", ()) or ("resource_enforcement_failed",)
                return ProcessResult("failed", process.returncode, "", ";".join(reason))
            resource_evidence = ("resource-controller-enforced",)
            resource_lease_id = resource_lease.lease_id if resource_lease is not None else None

        evidence = (*execution_evidence, "supervised-lifecycle-observed", *resource_evidence)
        try:
            stdout, stderr = process.communicate(timeout=policy.timeout)
        except subprocess.TimeoutExpired as exc:
            self._terminate(process)
            try:
                stdout, stderr = process.communicate(timeout=2.0)
            except subprocess.TimeoutExpired:
                self._kill(process)
                stdout, stderr = process.communicate()
            self._release(process.pid)
            return ProcessResult(
                "timed_out", process.returncode, stdout or exc.stdout or "",
                stderr or exc.stderr or "", True, backend="process-supervisor",
                execution_evidence=evidence, resource_lease_id=resource_lease_id,
            )

        self._release(process.pid)
        return ProcessResult(
            "succeeded" if process.returncode == 0 else "failed",
            process.returncode, stdout, stderr, backend="process-supervisor",
            execution_evidence=evidence, resource_lease_id=resource_lease_id,
        )

    def execute(self, argv: tuple[str, ...], *, admitted: bool = False,
                cwd: str | None = None, environment: Mapping[str, str] | None = None,
                policy: SupervisorPolicy | None = None,
                resource_lease: ResourceLease | None = None,
                resource_budget: ResourceBudget | None = None,
                execution_evidence: tuple[str, ...] = ()) -> ProcessResult:
        if not admitted:
            return ProcessResult("rejected", None, "", "execution scope is not admitted")
        if not argv or not argv[0]:
            raise ValueError("argv must contain an executable")
        policy = policy or SupervisorPolicy()
        reasons = policy.validate()
        if reasons:
            return ProcessResult("rejected", None, "", ";".join(reasons))
        budget = resource_budget or ResourceBudget()
        attempts = 1 + policy.max_restarts if policy.restart == "on-failure" else 1
        last = ProcessResult("failed", None, "", "no execution attempt")
        for attempt in range(attempts):
            last = self._once(
                argv, cwd=cwd, environment=environment, policy=policy,
                resource_lease=resource_lease, resource_budget=budget,
                execution_evidence=execution_evidence,
            )
            if last.status == "succeeded":
                return last
            if last.status == "timed_out" or policy.restart != "on-failure" or attempt + 1 >= attempts:
                return last
        return last
