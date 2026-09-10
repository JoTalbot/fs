"""Fail-closed Windows Job Object backend contract."""
from __future__ import annotations
from dataclasses import dataclass
import os
from .model import ResourceBudget
from .resource_control import ResourceLease

@dataclass(frozen=True, slots=True)
class WindowsJobPlan:
    available: bool
    enforceable: bool
    settings: dict[str, int]
    reasons: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class WindowsJobResult:
    applied: bool
    verified: bool
    pid: int | None
    settings: dict[str, int]
    reasons: tuple[str, ...] = ()

class WindowsJobObjectBackend:
    name = "windows-job-object"

    def plan(self, lease: ResourceLease | None, budget: ResourceBudget) -> WindowsJobPlan:
        settings = {k: v for k, v in {"memory_bytes": budget.memory_bytes, "cpu_millis": budget.cpu_millis, "pids": budget.pids, "disk_bytes": budget.disk_bytes}.items() if v is not None}
        if not settings:
            return WindowsJobPlan(os.name == "nt", True, {})
        if os.name != "nt":
            return WindowsJobPlan(False, False, {}, ("windows_required",))
        if lease is None:
            return WindowsJobPlan(True, False, {}, ("resource_lease_required",))
        errors = lease.validate()
        if errors:
            return WindowsJobPlan(True, False, {}, errors)
        if not lease.active:
            return WindowsJobPlan(True, False, {}, ("resource_lease_inactive",))
        if budget.disk_bytes is not None:
            return WindowsJobPlan(True, False, {}, ("disk_limit_unsupported",))
        return WindowsJobPlan(True, True, settings)

    def apply(self, pid: int, lease: ResourceLease, budget: ResourceBudget) -> WindowsJobResult:
        plan = self.plan(lease, budget)
        if not plan.enforceable:
            return WindowsJobResult(False, False, pid, {}, plan.reasons)
        return WindowsJobResult(False, False, pid, {}, ("native_job_attachment_not_implemented",))
