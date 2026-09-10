"""Explicit isolation backend contracts for FS execution.

Backends are opt-in. Capability observation never enables isolation implicitly,
and no backend may elevate privileges or mutate host policy. The Linux
namespace backend uses the platform's ``unshare`` utility when requested and
available; it does not attempt to acquire privileges.
"""
from __future__ import annotations

from dataclasses import dataclass
import platform
import shutil


@dataclass(frozen=True, slots=True)
class IsolationPlan:
    backend: str
    argv_prefix: tuple[str, ...]
    guarantees: tuple[str, ...]
    available: bool
    reason: str = ""


class IsolationBackend:
    name = "none"

    def plan(self) -> IsolationPlan:
        return IsolationPlan(self.name, (), (), True)


class LinuxNamespaceBackend(IsolationBackend):
    name = "linux-namespaces"

    def plan(self) -> IsolationPlan:
        if platform.system().lower() != "linux":
            return IsolationPlan(self.name, (), (), False, "host is not Linux")
        unshare = shutil.which("unshare")
        if unshare is None:
            return IsolationPlan(self.name, (), (), False, "unshare utility is unavailable")
        return IsolationPlan(
            self.name,
            (unshare, "--mount", "--pid", "--fork", "--mount-proc"),
            ("mount-namespace", "pid-namespace"),
            True,
            "kernel policy may still reject unprivileged namespace creation",
        )

    def wrap(self, argv: tuple[str, ...]) -> tuple[str, ...]:
        plan = self.plan()
        if not plan.available:
            raise RuntimeError(plan.reason)
        if not argv or not argv[0]:
            raise ValueError("argv must contain an executable")
        return plan.argv_prefix + argv


class WindowsJobObjectBackend(IsolationBackend):
    name = "windows-job-objects"

    def plan(self) -> IsolationPlan:
        available = platform.system().lower() == "windows"
        return IsolationPlan(
            self.name,
            (),
            ("job-object",) if available else (),
            available,
            "native Job Object binding is not yet implemented" if available else "host is not Windows",
        )


def current_isolation_backend() -> IsolationBackend:
    system = platform.system().lower()
    if system == "linux":
        return LinuxNamespaceBackend()
    if system == "windows":
        return WindowsJobObjectBackend()
    return IsolationBackend()
