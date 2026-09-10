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
        return {
            "platform": self.name,
            "architecture": self.architecture,
            "cpu": {"cores": self.cpu_cores},
            "features": dict(self.features),
        }


class PlatformAdapter:
    """Common interface implemented by concrete host-platform adapters."""

    name = "generic"

    def describe(self) -> PlatformDescriptor:
        return PlatformDescriptor(
            name=self.name,
            architecture=platform.machine().lower() or "unknown",
            cpu_cores=os.cpu_count() or 1,
            features={},
        )


class LinuxPlatformAdapter(PlatformAdapter):
    name = "linux"

    def describe(self) -> PlatformDescriptor:
        return PlatformDescriptor(
            name=self.name,
            architecture=platform.machine().lower() or "unknown",
            cpu_cores=os.cpu_count() or 1,
            features={
                "namespaces": os.path.isdir("/proc/self/ns"),
                "cgroups": os.path.isdir("/sys/fs/cgroup"),
            },
        )


class WindowsPlatformAdapter(PlatformAdapter):
    name = "windows"

    def describe(self) -> PlatformDescriptor:
        return PlatformDescriptor(
            name=self.name,
            architecture=platform.machine().lower() or "unknown",
            cpu_cores=os.cpu_count() or 1,
            features={
                "job_objects": True,
            },
        )


def current_platform_adapter() -> PlatformAdapter:
    system = platform.system().lower()
    if system == "linux":
        return LinuxPlatformAdapter()
    if system == "windows":
        return WindowsPlatformAdapter()
    return PlatformAdapter()
