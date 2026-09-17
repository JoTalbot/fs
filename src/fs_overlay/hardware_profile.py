"""Narrow host/hardware capability abstraction.

The adapter exposes only stable, non-identifying host facts. It deliberately
avoids serial numbers, MAC addresses, device identifiers, and other values that
would turn a capability fingerprint into a machine identity.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
from typing import Mapping


@dataclass(frozen=True, slots=True)
class HardwareProfile:
    """Stable host capability facts suitable for scheduling and diagnostics."""

    architecture: str
    cpu_cores: int
    memory_bytes: int | None
    features: Mapping[str, bool]

    def to_dict(self) -> dict[str, object]:
        return {
            "architecture": self.architecture,
            "cpu_cores": self.cpu_cores,
            "memory_bytes": self.memory_bytes,
            "features": dict(sorted(self.features.items())),
        }


class HardwareCapabilityAdapter:
    """Observe conservative hardware facts without claiming ownership."""

    def describe(self) -> HardwareProfile:
        memory_bytes: int | None = None
        if platform.system().lower() == "linux":
            try:
                for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                    if line.startswith("MemTotal:"):
                        memory_bytes = int(line.split()[1]) * 1024
                        break
            except (OSError, ValueError, IndexError):
                memory_bytes = None
        return HardwareProfile(
            architecture=platform.machine().lower() or "unknown",
            cpu_cores=os.cpu_count() or 1,
            memory_bytes=memory_bytes,
            features={},
        )


def hardware_capability_fingerprint(profile: HardwareProfile) -> str:
    """Return a deterministic SHA-256 capability fingerprint."""
    canonical = json.dumps(
        profile.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
