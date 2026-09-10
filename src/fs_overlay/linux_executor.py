"""Explicit Linux namespace execution adapter.

This adapter is intentionally narrow: it executes only when the caller has
already admitted the operation and explicitly selected Linux namespaces. It
never invokes a shell, escalates privileges, changes host policy, or treats
`unshare` availability as proof that the kernel will permit isolation.
"""
from __future__ import annotations

from dataclasses import dataclass
import subprocess
from typing import Mapping

from .adapter import ProcessResult
from .isolation import LinuxNamespaceBackend


@dataclass(frozen=True, slots=True)
class LinuxExecutionPolicy:
    """Explicit policy for the namespace reference executor."""

    filesystem: str = "host"
    network: str = "host"


class LinuxNamespaceExecutor:
    """Execute an already-admitted command through Linux namespaces."""

    def __init__(self, backend: LinuxNamespaceBackend | None = None) -> None:
        self.backend = backend or LinuxNamespaceBackend()

    def execute(
        self,
        argv: tuple[str, ...],
        *,
        admitted: bool = False,
        cwd: str | None = None,
        environment: Mapping[str, str] | None = None,
        timeout: float = 30.0,
        policy: LinuxExecutionPolicy | None = None,
    ) -> ProcessResult:
        if not admitted:
            return ProcessResult("rejected", None, "", "execution scope is not admitted")
        if not argv or not argv[0]:
            raise ValueError("argv must contain an executable")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        policy = policy or LinuxExecutionPolicy()
        if policy.filesystem != "host" or policy.network != "host":
            return ProcessResult(
                "rejected", None, "", "requested filesystem/network policy is not enforced by this backend"
            )

        try:
            wrapped = self.backend.wrap(argv)
        except RuntimeError as exc:
            return ProcessResult("rejected", None, "", str(exc))

        env = None
        if environment is not None:
            import os
            env = os.environ.copy()
            env.update(environment)
        try:
            completed = subprocess.run(
                list(wrapped),
                cwd=cwd,
                env=env,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return ProcessResult("timed_out", None, exc.stdout or "", exc.stderr or "", True)
        return ProcessResult(
            "succeeded" if completed.returncode == 0 else "failed",
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )
