"""Explicit isolation backend contracts for FS execution.

Backends are opt-in. Capability observation never enables isolation implicitly,
and no backend may elevate privileges or mutate host policy. Linux namespace
execution uses the platform's ``unshare`` utility for the reference namespace
backend; workspace isolation is a separate, explicit bubblewrap backend.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import platform
import shutil
import subprocess


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


class BubblewrapWorkspaceBackend(IsolationBackend):
    """Explicit workspace filesystem backend using bubblewrap.

    Bubblewrap creates the mount namespace and exposes only explicitly bound
    paths. The backend is deliberately opt-in because normal unprivileged bwrap
    operation uses a user namespace. FS never enables that mechanism silently.

    The wrapped command performs filesystem and, when requested, network
    namespace observations before and after the workload in the same sandbox.
    Reserved wrapper exit codes mean that an observation failed, so the
    transaction layer can fail closed without confusing a disposable
    capability probe with execution evidence.
    """

    name = "bubblewrap-workspace"
    minimum_version = (0, 12, 0)
    boundary_check_exit_codes = (125, 126)
    _runtime_roots = ("/usr", "/bin", "/lib", "/lib64", "/etc")
    _boundary_script = (
        'host_path="$1"; expected_net_ns="$2"; network_mode="$3"; shift 3; '
        'test -d /workspace && test ! -e "$host_path" || exit 125; '
        'if [ "$network_mode" = "deny" ]; then '
        'test "$(readlink /proc/self/ns/net)" != "$expected_net_ns" || exit 125; fi; '
        '"$@"; status=$?; '
        'test -d /workspace && test ! -e "$host_path" || exit 126; '
        'if [ "$network_mode" = "deny" ]; then '
        'test "$(readlink /proc/self/ns/net)" != "$expected_net_ns" || exit 126; fi; '
        'exit "$status"'
    )

    def _binary(self) -> str | None:
        if platform.system().lower() != "linux":
            return None
        return shutil.which("bwrap")

    def _version(self, binary: str) -> tuple[int, int, int] | None:
        try:
            completed = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        token = completed.stdout.strip().split()[-1] if completed.stdout.strip() else ""
        parts = token.split(".")
        if len(parts) < 2 or not all(part.isdigit() for part in parts[:2]):
            return None
        patch = parts[2] if len(parts) > 2 else "0"
        if not patch.isdigit():
            return None
        return int(parts[0]), int(parts[1]), int(patch)

    def _workspace_overlaps_runtime_root(self, workspace: Path) -> bool:
        resolved = workspace.resolve()
        return any(
            resolved == Path(root) or Path(root) in resolved.parents
            for root in self._runtime_roots
        )

    def plan(
        self,
        workspace_path: str | None = None,
        *,
        network: str = "deny",
        read_only: bool = True,
    ) -> IsolationPlan:
        binary = self._binary()
        if binary is None:
            return IsolationPlan(self.name, (), (), False, "bubblewrap utility is unavailable")
        version = self._version(binary)
        if version is None:
            return IsolationPlan(self.name, (), (), False, "bubblewrap version is unknown")
        if version < self.minimum_version:
            return IsolationPlan(self.name, (), (), False, "bubblewrap version is below 0.12.0")
        if not workspace_path:
            return IsolationPlan(self.name, (), (), False, "workspace_path_required")
        if network not in {"host", "deny"}:
            return IsolationPlan(self.name, (), (), False, "unsupported network policy")
        path = Path(workspace_path)
        if not path.is_absolute():
            return IsolationPlan(self.name, (), (), False, "workspace_path_must_be_absolute")
        if not path.is_dir():
            return IsolationPlan(self.name, (), (), False, "workspace_path_not_directory")
        if self._workspace_overlaps_runtime_root(path):
            return IsolationPlan(self.name, (), (), False, "workspace_path_overlaps_runtime_root")
        return IsolationPlan(
            self.name,
            self._prefix(binary, path, network=network, read_only=read_only),
            ("workspace-filesystem-boundary",),
            True,
            "explicit bubblewrap workspace backend",
        )

    def _prefix(
        self,
        binary: str,
        workspace: Path,
        *,
        network: str,
        read_only: bool,
    ) -> tuple[str, ...]:
        prefix: list[str] = [
            binary,
            "--die-with-parent",
            "--new-session",
            "--unshare-pid",
        ]
        if network == "deny":
            prefix.append("--unshare-net")
        prefix.extend(
            (
                "--ro-bind" if read_only else "--bind",
                str(workspace),
                "/workspace",
                "--proc",
                "/proc",
                "--dev",
                "/dev",
            )
        )
        for root in self._runtime_roots:
            if os.path.exists(root):
                prefix.extend(("--ro-bind", root, root))
        prefix.extend(("--chdir", "/workspace"))
        return tuple(prefix)

    def wrap(
        self,
        argv: tuple[str, ...],
        *,
        workspace_path: str,
        network: str = "deny",
        read_only: bool = True,
    ) -> tuple[str, ...]:
        plan = self.plan(
            workspace_path,
            network=network,
            read_only=read_only,
        )
        if not plan.available:
            raise RuntimeError(plan.reason)
        if not argv or not argv[0]:
            raise ValueError("argv must contain an executable")
        parent_net_ns = os.readlink("/proc/self/ns/net") if network == "deny" else "host"
        return plan.argv_prefix + (
            "--",
            "/bin/sh",
            "-c",
            self._boundary_script,
            "fs-boundary",
            workspace_path,
            parent_net_ns,
            network,
            *argv,
        )


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
