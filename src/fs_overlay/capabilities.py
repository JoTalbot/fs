"""Conservative local capability discovery for the FS reference node."""
from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LocalCapabilities:
    platform: str
    architecture: str
    cpu_cores: int
    memory_bytes: int | None

    def to_dict(self) -> dict[str, object]:
        return {
            "platform": self.platform,
            "architecture": self.architecture,
            "cpu": {"cores": self.cpu_cores},
            "memory": {"bytes": self.memory_bytes},
        }


def _linux_memory_bytes() -> int | None:
    path = Path("/proc/meminfo")
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition(":")
            if key == "MemTotal":
                fields = value.strip().split()
                if fields and fields[0].isdigit():
                    return int(fields[0]) * 1024
    except (OSError, UnicodeError):
        return None
    return None


def discover_local_capabilities() -> LocalCapabilities:
    system = platform.system().lower() or "unknown"
    memory = _linux_memory_bytes() if system == "linux" else None
    return LocalCapabilities(
        platform=system,
        architecture=platform.machine().lower() or "unknown",
        cpu_cores=os.cpu_count() or 1,
        memory_bytes=memory,
    )
