"""Explicit workspace boundary contracts for FS execution.

A workspace is a logical FS object, not merely an arbitrary host path. The
control plane may describe a host binding only when ownership/delegation has
already been established. This module does not create directories, mount
filesystems, change permissions, or mutate host state.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True, slots=True)
class WorkspaceBinding:
    """A previously admitted mapping from an FS workspace to a host path."""

    workspace_id: str
    host_path: str
    owned_or_delegated: bool = False
    read_only: bool = False

    def validate(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.workspace_id:
            reasons.append("workspace_id_required")
        if not self.host_path:
            reasons.append("workspace_path_required")
        elif not os.path.isabs(self.host_path):
            reasons.append("workspace_path_must_be_absolute")
        if not self.owned_or_delegated:
            reasons.append("workspace_ownership_or_delegation_required")
        return tuple(reasons)


@dataclass(frozen=True, slots=True)
class WorkspacePlan:
    """Descriptive workspace admission result. It never mutates the host."""

    binding: WorkspaceBinding
    admitted: bool
    path: Path | None
    reasons: tuple[str, ...] = ()


def plan_workspace(binding: WorkspaceBinding) -> WorkspacePlan:
    """Validate an already-established workspace binding.

    Existence is observed but is not treated as ownership. The caller must
    explicitly provide an ownership/delegation fact before admission.
    """
    reasons = list(binding.validate())
    if not reasons:
        path = Path(binding.host_path)
        if not path.exists():
            reasons.append("workspace_path_not_found")
        elif not path.is_dir():
            reasons.append("workspace_path_not_directory")
    else:
        path = None
    return WorkspacePlan(binding, not reasons, path if not reasons else None, tuple(reasons))
