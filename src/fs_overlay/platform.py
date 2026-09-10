"""Platform adapter boundary for observable local capabilities.

This module deliberately stops at observation. It does not claim isolation,
privilege, or resource ownership. Those semantics belong to explicit backend
adapters such as Linux namespaces/cgroups and Windows Job Objects.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import platform
from typing import Mapping


@dataclass(frozen=True, slots=True)
class PlatformDescriptor:
    name: str
    architecture: str
    cpu_cores: int
    features: Mapping[str, bool]

    def to_dict(self) -> dict[str, object]:
        return {"platform": self.name, "architecture": self.architecture, "cpu": {"cores": self.cpu_cores}, "features": dict(self.features)}


class PlatformAdapter:
    name = "generic"

    def describe(self) -> PlatformDescriptor:
        return PlatformDescriptor(self.name, platform.machine().lower() or "unknown", os.cpu_count() or 1, {})


class LinuxPlatformAdapter(PlatformAdapter):
    name = "linux"

    def describe(self) -> PlatformDescriptor:
        return PlatformDescriptor(self.name, platform.machine().lower() or "unknown", os.cpu_count() or 1, {"namespaces": os.path.isdir("/proc/self/ns"), "cgroups": os.path.isdir("/sys/fs/cgroup")})


class WindowsPlatformAdapter(PlatformAdapter):
    name = "windows"

    def describe(self) -> PlatformDescriptor:
        return PlatformDescriptor(self.name, platform.machine().lower() or "unknown", os.cpu_count() or 1, {"job_objects": True})


class MacOSPlatformAdapter(PlatformAdapter):
    name = "darwin"


class FreeBSDPlatformAdapter(PlatformAdapter):
    name = "freebsd"


def current_platform_adapter() -> PlatformAdapter:
    system = platform.system().lower()
    if system == "linux":
        return LinuxPlatformAdapter()
    if system == "windows":
        return WindowsPlatformAdapter()
    if system == "darwin":
        return MacOSPlatformAdapter()
    if system == "freebsd":
        return FreeBSDPlatformAdapter()
    return PlatformAdapter()
