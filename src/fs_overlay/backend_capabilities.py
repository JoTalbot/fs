"""Platform/backend capability negotiation for execution adapters.

Negotiation reports what a native backend can actually enforce. It never
turns an unavailable mechanism into an optimistic capability claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import platform

from .windows_job import WindowsJobObjectBackend


@dataclass(frozen=True, slots=True)
class BackendCapabilities:
    platform: str
    resource_backend: str | None
    resources: tuple[str, ...]
    filesystem_isolation: tuple[str, ...]
    network_isolation: tuple[str, ...]
    reasons: tuple[str, ...] = ()


def negotiate_backend_capabilities() -> BackendCapabilities:
    system = platform.system().lower()
    if os.name == "nt":
        backend = WindowsJobObjectBackend()
        return BackendCapabilities(system, backend.name, ("cpu_millis", "memory_bytes", "pids"), (), ())
    if system == "linux":
        return BackendCapabilities(system, "linux-cgroup-v2", ("cpu_millis", "memory_bytes", "pids"), ("workspace-only",), ("deny", "host"))
    if system == "darwin":
        return BackendCapabilities(system, None, (), (), (), ("macos_signed_sandbox_runtime_required",))
    return BackendCapabilities(system, None, (), (), (), ("native_backend_unavailable",))
