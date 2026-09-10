"""Conservative runtime probes for Linux namespace capabilities.

A probe is observational only. It runs a tiny disposable command through
``unshare`` when available and records the actual namespace identity. Probe
success is not treated as proof of a stronger filesystem boundary than the
probe tests.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
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

    namespace_link = {"mount": "mnt", "pid": "pid", "net": "net"}[namespace]
    parent_namespace = os.readlink(f"/proc/self/ns/{namespace_link}")
    flag = {"mount": "--mount", "pid": "--pid", "net": "--net"}[namespace]
    command = [
        unshare,
        flag,
        "--fork",
        "--",
        "readlink",
        f"/proc/self/ns/{namespace_link}",
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return NamespaceProbeResult(namespace, False, None, "probe_timed_out")

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "probe_failed").strip()
        return NamespaceProbeResult(namespace, False, completed.returncode, detail)

    child_namespace = completed.stdout.strip()
    if not child_namespace:
        return NamespaceProbeResult(namespace, False, completed.returncode, "namespace_identity_missing")
    if child_namespace == parent_namespace:
        return NamespaceProbeResult(namespace, False, completed.returncode, "namespace_identity_unchanged")
    return NamespaceProbeResult(namespace, True, completed.returncode, "namespace_identity_changed")
