"""Explicit host execution adapter for the reference runtime.

Only an already-admitted operation may reach this adapter. Commands are passed
as argv without a shell, and execution is bounded by timeout/cwd/environment.
The adapter does not elevate privileges or modify system configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import platform
import subprocess
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ProcessResult:
    status: str
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool = False


class NativeProcessAdapter:
    name = "native-process"

    @staticmethod
    def capability_fingerprint() -> dict[str, str]:
        return {
            "platform": platform.system().lower(),
            "architecture": platform.machine().lower(),
            "python": platform.python_version(),
        }

    def execute(
        self,
        argv: tuple[str, ...],
        *,
        cwd: str | None = None,
        environment: Mapping[str, str] | None = None,
        timeout: float = 30.0,
    ) -> ProcessResult:
        if not argv or not argv[0]:
            raise ValueError("argv must contain an executable")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        env = os.environ.copy()
        if environment is not None:
            env.update(environment)
        try:
            completed = subprocess.run(
                list(argv),
                cwd=cwd,
                env=env,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return ProcessResult(
                status="timed_out",
                returncode=None,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                timed_out=True,
            )
        return ProcessResult(
            status="succeeded" if completed.returncode == 0 else "failed",
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
