"""Explicit Linux cgroup v2 resource enforcement inside delegated scopes.

The backend never creates or discovers a host-wide control group. A caller must
present an active resource lease whose scope is an existing absolute cgroup
v2 directory. The backend writes only controller files inside that exact scope
and reads them back before reporting enforcement evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import platform

from .model import ResourceBudget
from .resource_control import ResourceLease


@dataclass(frozen=True, slots=True)
class CgroupV2Plan:
    available: bool
    enforceable: bool
    scope: str | None
    settings: tuple[tuple[str, str], ...] = ()
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CgroupV2Result:
    applied: bool
    verified: bool
    pid: int
    settings: tuple[tuple[str, str], ...] = ()
    reasons: tuple[str, ...] = ()


class LinuxCgroupV2Backend:
    """Apply portable resource budgets only inside an explicit lease scope."""

    name = "linux-cgroup-v2"
    cpu_period_us = 100_000

    def _scope_path(self, lease: ResourceLease) -> Path:
        path = Path(lease.scope)
        if not path.is_absolute():
            raise ValueError("resource lease scope must be absolute")
        resolved = path.resolve(strict=True)
        if resolved != path:
            raise ValueError("resource lease scope must not be a symlink")
        if not resolved.is_dir():
            raise ValueError("resource lease scope must be a directory")
        return resolved

    def _settings(self, budget: ResourceBudget) -> tuple[tuple[str, str], ...]:
        settings: list[tuple[str, str]] = []
        if budget.cpu_millis is not None:
            if budget.cpu_millis <= 0:
                raise ValueError("cpu_millis must be positive")
            quota = budget.cpu_millis * self.cpu_period_us // 1000
            settings.append(("cpu.max", f"{quota} {self.cpu_period_us}"))
        if budget.memory_bytes is not None:
            if budget.memory_bytes <= 0:
                raise ValueError("memory_bytes must be positive")
            settings.append(("memory.max", str(budget.memory_bytes)))
        if budget.pids is not None:
            if budget.pids <= 0:
                raise ValueError("pids must be positive")
            settings.append(("pids.max", str(budget.pids)))
        if budget.disk_bytes is not None:
            raise ValueError("disk_bytes is not supported by cgroup v2 resource controllers")
        return tuple(settings)

    def plan(self, lease: ResourceLease | None, budget: ResourceBudget) -> CgroupV2Plan:
        if platform.system().lower() != "linux":
            return CgroupV2Plan(False, False, None, reasons=("host_is_not_linux",))
        if lease is None:
            return CgroupV2Plan(False, False, None, reasons=("resource_lease_required",))
        errors = lease.validate()
        if errors:
            return CgroupV2Plan(False, False, None, reasons=errors)
        if not lease.active:
            return CgroupV2Plan(False, False, None, reasons=("resource_lease_inactive",))
        try:
            scope = self._scope_path(lease)
            settings = self._settings(budget)
        except (OSError, ValueError) as exc:
            return CgroupV2Plan(False, False, None, reasons=(str(exc),))

        controllers_file = scope / "cgroup.controllers"
        procs_file = scope / "cgroup.procs"
        if not controllers_file.is_file() or not procs_file.is_file():
            return CgroupV2Plan(
                False,
                False,
                str(scope),
                settings,
                ("cgroup_v2_scope_not_detected",),
            )
        missing = tuple(name for name, _ in settings if not (scope / name).is_file())
        if missing:
            return CgroupV2Plan(
                False,
                False,
                str(scope),
                settings,
                ("required_controller_unavailable:" + ",".join(missing),),
            )
        if not os.access(procs_file, os.W_OK):
            return CgroupV2Plan(
                False,
                False,
                str(scope),
                settings,
                ("cgroup_procs_not_writable",),
            )
        unwritable = tuple(name for name, _ in settings if not os.access(scope / name, os.W_OK))
        if unwritable:
            return CgroupV2Plan(
                False,
                False,
                str(scope),
                settings,
                ("controller_not_writable:" + ",".join(unwritable),),
            )
        return CgroupV2Plan(True, True, str(scope), settings)

    def apply(self, pid: int, lease: ResourceLease | None, budget: ResourceBudget) -> CgroupV2Result:
        if pid <= 0:
            raise ValueError("pid must be positive")
        plan = self.plan(lease, budget)
        if not plan.enforceable or plan.scope is None:
            return CgroupV2Result(False, False, pid, plan.settings, plan.reasons)

        scope = Path(plan.scope)
        try:
            for name, value in plan.settings:
                (scope / name).write_text(value + "\n", encoding="ascii")
            (scope / "cgroup.procs").write_text(str(pid) + "\n", encoding="ascii")
        except OSError as exc:
            return CgroupV2Result(
                False,
                False,
                pid,
                plan.settings,
                (f"cgroup_write_failed:{type(exc).__name__}",),
            )

        for name, expected in plan.settings:
            try:
                observed = (scope / name).read_text(encoding="ascii").strip()
            except OSError as exc:
                return CgroupV2Result(
                    True,
                    False,
                    pid,
                    plan.settings,
                    (f"cgroup_readback_failed:{type(exc).__name__}",),
                )
            if observed != expected:
                return CgroupV2Result(
                    True,
                    False,
                    pid,
                    plan.settings,
                    (f"cgroup_readback_mismatch:{name}",),
                )
        return CgroupV2Result(True, True, pid, plan.settings)
