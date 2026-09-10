"""Lower declarative execution policy into backend-specific launch plans.

Lowering is descriptive. It never executes a process, grants authority, or
claims guarantees that the selected backend cannot enforce.
"""
from __future__ import annotations

from dataclasses import dataclass

from .isolation import IsolationBackend, LinuxNamespaceBackend, WindowsJobObjectBackend
from .model import EnvironmentSpec


@dataclass(frozen=True, slots=True)
class LoweredExecution:
    backend: str
    argv: tuple[str, ...]
    cwd: str | None
    environment: tuple[tuple[str, str], ...]
    guarantees: tuple[str, ...] = ()


def lower_environment(spec: EnvironmentSpec, backend: IsolationBackend) -> LoweredExecution:
    """Translate an EnvironmentSpec into a bounded launch description.

    Only semantics actually represented by the backend are lowered. Policies
    that require stronger isolation are rejected instead of silently weakened.
    """
    if not spec.command or not spec.command[0]:
        raise ValueError("environment command must contain an executable")

    policy = spec.policy
    if policy.allow_privileged:
        raise ValueError("privileged execution requires an explicit privileged backend")
    if policy.devices:
        raise ValueError("device policy requires a device-aware backend")
    if policy.resources.cpu_millis is not None or policy.resources.memory_bytes is not None or policy.resources.pids is not None:
        raise ValueError("resource limits require a resource-controller backend")

    if isinstance(backend, LinuxNamespaceBackend):
        if policy.filesystem != "host":
            raise ValueError("Linux namespace backend does not yet enforce workspace filesystem boundaries")
        if policy.network != "host":
            raise ValueError("Linux namespace backend does not yet enforce network policy")
        argv = backend.wrap(spec.command)
        guarantees = backend.plan().guarantees
    elif isinstance(backend, WindowsJobObjectBackend):
        raise ValueError("Windows Job Object execution binding is not implemented")
    else:
        if policy.filesystem != "host" or policy.network != "host":
            raise ValueError("native backend cannot enforce requested isolation policy")
        argv = spec.command
        guarantees = ()

    return LoweredExecution(
        backend=backend.name,
        argv=argv,
        cwd=None,
        environment=tuple(sorted(spec.environment.items())),
        guarantees=tuple(guarantees),
    )
