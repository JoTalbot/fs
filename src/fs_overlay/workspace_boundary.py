"""Disposable evidence probe for an exact workspace filesystem boundary.

The probe is intentionally independent from the execution planner. It uses
bubblewrap only when that explicit host backend is installed and verifies the
property that a disposable sandbox exposes the admitted workspace while an
unbound host path is absent. It never enables user namespaces as a fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile


@dataclass(frozen=True, slots=True)
class WorkspaceBoundaryProbeResult:
    supported: bool
    returncode: int | None
    detail: str


def probe_workspace_boundary(*, timeout: float = 5.0) -> WorkspaceBoundaryProbeResult:
    """Verify a disposable workspace root using an explicitly installed bwrap backend."""
    if platform.system().lower() != "linux":
        return WorkspaceBoundaryProbeResult(False, None, "host_is_not_linux")
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        return WorkspaceBoundaryProbeResult(False, None, "bubblewrap_unavailable")

    with tempfile.TemporaryDirectory(prefix="fs-workspace-probe-") as workspace:
        workspace_path = Path(workspace)
        sentinel = workspace_path / "sentinel"
        sentinel.write_text("workspace", encoding="utf-8")
        command = [
            bwrap,
            "--die-with-parent",
            "--new-session",
            "--unshare-pid",
            "--unshare-net",
            "--ro-bind",
            str(workspace_path),
            "/workspace",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--ro-bind",
            "/bin",
            "/bin",
            "--ro-bind",
            "/usr",
            "/usr",
            "--ro-bind",
            "/lib",
            "/lib",
            "--ro-bind",
            "/lib64",
            "/lib64",
            "--chdir",
            "/workspace",
            "--",
            "/bin/sh",
            "-c",
            "test -f /workspace/sentinel && test ! -e /fs-host-sentinel",
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
            return WorkspaceBoundaryProbeResult(False, None, "probe_timed_out")

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "workspace_boundary_probe_failed").strip()
        return WorkspaceBoundaryProbeResult(False, completed.returncode, detail)
    return WorkspaceBoundaryProbeResult(True, completed.returncode, "workspace_visible_host_root_absent")
