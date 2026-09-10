"""Conservative runtime probes for Linux namespace capabilities.

A probe is observational only. It runs a tiny disposable command through
``unshare`` when available and records the actual result. Probe success is
not treated as proof of a stronger filesystem boundary than the probe tests.
"""
from __future__ import annotations

from dataclasses import dataclass
import platform
import shutil
import subprocess


@dataclass(frozen=True, slots=True)
class NamespaceProbeResult:
    namespace: str
    supported: bool
    returncode: int | None
    detail: str


def probe_namespace(namespace: str, *, timeout: float = 5.0) -> NamespaceProbeResult:
    if namespace not in {"mount", "pid", "net"}:
        raise ValueError("unsupported namespace probe")
    if platform.system().lower() != "linux":
        return NamespaceProbeResult(namespace, False, None, "host_is_not_linux")
    unshare = shutil.which("unshare")
    if unshare is None:
        return NamespaceProbeResult(namespace, False, None, "unshare_utility_unavailable")
    flag = {"mount": "--mount", "pid": "--pid", "net": "--net"}[namespace]
    try:
        completed = subprocess.run(
            [unshare, flag, "--", "true"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return NamespaceProbeResult(namespace, False, None, "probe_timed_out")
    if completed.returncode == 0:
        return NamespaceProbeResult(namespace, True, 0, "probe_succeeded")
    detail = (completed.stderr or completed.stdout or "probe_failed").strip()
    return NamespaceProbeResult(namespace, False, completed.returncode, detail)
