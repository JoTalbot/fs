"""Explicit host execution adapter for the reference runtime.

The adapter refuses to execute unless the caller supplies an already-admitted
execution scope. Commands are passed as argv without a shell and bounded by
timeout/cwd/environment. No privilege elevation or system configuration is
performed here.
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
    backend: str = "native-process"
    execution_evidence: tuple[str, ...] = ()


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
        admitted: bool = False,
        cwd: str | None = None,
        environment: Mapping[str, str] | None = None,
        timeout: float = 30.0,
    ) -> ProcessResult:
        if not admitted:
            return ProcessResult("rejected", None, "", "execution scope is not admitted")
        if not argv or not argv[0]:
            raise ValueError("argv must contain an executable")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        env = os.environ.copy()
        if environment is not None:
            env.update(environment)
        try:
            completed = subprocess.run(
                list(argv), cwd=cwd, env=env, shell=False,
                capture_output=True, text=True, timeout=timeout, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return ProcessResult("timed_out", None, exc.stdout or "", exc.stderr or "", True)
        return ProcessResult(
            "succeeded" if completed.returncode == 0 else "failed",
            completed.returncode, completed.stdout, completed.stderr,
        )
