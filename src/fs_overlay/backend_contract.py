"""Versioned contract shared by concrete execution backends.

A backend is considered compatible only when its contract version is known and
its advertised evidence markers are explicit. Capability negotiation remains
separate from execution evidence.
"""
from __future__ import annotations

from dataclasses import dataclass


BACKEND_CONTRACT_VERSION = 1


@dataclass(frozen=True, slots=True)
class BackendContract:
    backend_id: str
    version: int
    evidence_markers: tuple[str, ...]
    resource_types: tuple[str, ...] = ()

    def compatible_with(self, version: int = BACKEND_CONTRACT_VERSION) -> bool:
        return self.version == version


LINUX_BUBBLEWRAP_CONTRACT = BackendContract(
    backend_id="bubblewrap-workspace",
    version=BACKEND_CONTRACT_VERSION,
    evidence_markers=("workspace-filesystem-boundary-observed", "network-namespace-observed"),
)

LINUX_CGROUP_V2_CONTRACT = BackendContract(
    backend_id="linux-cgroup-v2",
    version=BACKEND_CONTRACT_VERSION,
    evidence_markers=("resource-controller-enforced",),
    resource_types=("cpu_millis", "memory_bytes", "pids"),
)

WINDOWS_JOB_OBJECT_CONTRACT = BackendContract(
    backend_id="windows-job-object",
    version=BACKEND_CONTRACT_VERSION,
    evidence_markers=("resource-controller-enforced",),
    resource_types=("cpu_millis", "memory_bytes", "pids"),
)
