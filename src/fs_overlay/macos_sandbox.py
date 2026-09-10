"""macOS signed App Sandbox helper admission checks.

FS cannot turn a normal Python process into an App Sandbox process. macOS
sandboxing is established by signed executable entitlements and inherited by a
bundled helper launched by a sandboxed host. This module validates that
packaging boundary and never advertises it as active isolation for Python.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import platform
import subprocess

@dataclass(frozen=True, slots=True)
class MacOSSandboxInspection:
    available: bool
    helper: str
    host: str
    guarantees: tuple[str, ...] = ()
    reason: str = ""

class MacOSSignedHelperBackend:
    name = "macos-signed-sandbox-helper"
    required_helper_entitlements = ("com.apple.security.app-sandbox", "com.apple.security.inherit")
    required_host_entitlements = ("com.apple.security.app-sandbox",)

    def _codesign(self, args: list[str], target: Path) -> str | None:
        try:
            completed = subprocess.run(["codesign", *args, str(target)], capture_output=True, text=True, timeout=5.0, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return completed.stdout + completed.stderr if completed.returncode == 0 else None

    def _entitlements(self, target: Path) -> str | None:
        return self._codesign(["-d", "--entitlements", "-"], target)

    def inspect(self, helper_path: str, host_app_path: str) -> MacOSSandboxInspection:
        helper, host = Path(helper_path), Path(host_app_path)
        if platform.system().lower() != "darwin":
            return MacOSSandboxInspection(False, str(helper), str(host), reason="host is not macOS")
        if not helper.is_file():
            return MacOSSandboxInspection(False, str(helper), str(host), reason="helper_not_found")
        if not host.is_dir() or host.suffix != ".app":
            return MacOSSandboxInspection(False, str(helper), str(host), reason="sandbox_host_app_required")
        helper_entitlements = self._entitlements(helper)
        host_entitlements = self._entitlements(host)
        helper_signature = self._codesign(["--verify", "--strict", "--verbose=2"], helper)
        host_signature = self._codesign(["--verify", "--deep", "--strict", "--verbose=2"], host)
        helper_runtime = self._codesign(["--verify", "--strict", "--verbose=4"], helper)
        if None in (helper_entitlements, host_entitlements, helper_signature, host_signature, helper_runtime):
            return MacOSSandboxInspection(False, str(helper), str(host), reason="codesign_validation_failed")
        missing_helper = [key for key in self.required_helper_entitlements if f"<key>{key}</key>" not in helper_entitlements]
        missing_host = [key for key in self.required_host_entitlements if f"<key>{key}</key>" not in host_entitlements]
        if missing_helper:
            return MacOSSandboxInspection(False, str(helper), str(host), reason=f"missing_helper_entitlements:{','.join(missing_helper)}")
        if missing_host:
            return MacOSSandboxInspection(False, str(helper), str(host), reason=f"missing_host_entitlements:{','.join(missing_host)}")
        if "flags=0x10000(runtime)" not in helper_runtime:
            return MacOSSandboxInspection(False, str(helper), str(host), reason="helper_hardened_runtime_required")
        return MacOSSandboxInspection(True, str(helper), str(host), ("signed-sandbox-helper-admitted", "helper-sandbox-inheritance-configured"), "validated packaging boundary; host must launch helper")

    def plan(self, helper_path: str | None = None, host_app_path: str | None = None) -> MacOSSandboxInspection:
        if helper_path is None or host_app_path is None:
            return MacOSSandboxInspection(False, helper_path or "", host_app_path or "", reason="signed_helper_and_host_required")
        return self.inspect(helper_path, host_app_path)
