"""Plan a Linux mount namespace around an explicitly admitted workspace.

The planner is intentionally non-mutating. It produces an argv prefix for a
small helper that must perform mounts only after the FS workspace binding has
already been admitted. Host paths are never treated as mountable authority by
themselves.
"""
from __future__ import annotations

from dataclasses import dataclass
import platform
import shutil

from .workspace import WorkspaceBinding, plan_workspace


@dataclass(frozen=True, slots=True)
class MountNamespacePlan:
    available: bool
    admitted: bool
    backend: str = "linux-mount-namespace"
    argv_prefix: tuple[str, ...] = ()
    workspace_path: str | None = None
    read_only: bool = False
    guarantees: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


def plan_mount_namespace(binding: WorkspaceBinding) -> MountNamespacePlan:
    """Describe a mount-namespace launch without changing host state."""
    reasons = list(plan_workspace(binding).reasons)
    if platform.system().lower() != "linux":
        reasons.append("host_is_not_linux")
    unshare = shutil.which("unshare")
    if unshare is None:
        reasons.append("unshare_utility_unavailable")

    if reasons:
        return MountNamespacePlan(
            available=not any(r in {"host_is_not_linux", "unshare_utility_unavailable"} for r in reasons),
            admitted=False,
            reasons=tuple(reasons),
        )

    return MountNamespacePlan(
        available=True,
        admitted=True,
        argv_prefix=(unshare, "--mount", "--pid", "--fork", "--mount-proc"),
        workspace_path=binding.host_path,
        read_only=binding.read_only,
        guarantees=("mount-namespace", "pid-namespace", "workspace-binding-admitted"),
    )
