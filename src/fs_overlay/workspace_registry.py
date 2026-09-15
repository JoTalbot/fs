"""Deterministic managed-workspace registration and health state.

This module is deliberately plan/state only. Registration does not create,
move, mount, delete, or otherwise mutate host files. Host access remains
bounded by an explicitly admitted ``WorkspaceBinding``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .workspace import WorkspaceBinding, WorkspacePlan, plan_workspace


class WorkspaceMode(str, Enum):
    OBSERVED = "observed"
    MANAGED = "managed"


class WorkspaceHealth(str, Enum):
    HEALTHY = "healthy"
    NOT_FOUND = "not_found"
    NOT_DIRECTORY = "not_directory"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class WorkspaceRecord:
    """Registered logical workspace and its last observed health."""

    binding: WorkspaceBinding
    mode: WorkspaceMode
    health: WorkspaceHealth
    path: Path | None = None


def workspace_health(plan: WorkspacePlan) -> WorkspaceHealth:
    """Map an admission observation to a stable health state."""
    if plan.admitted:
        return WorkspaceHealth.HEALTHY
    if "workspace_path_not_found" in plan.reasons:
        return WorkspaceHealth.NOT_FOUND
    if "workspace_path_not_directory" in plan.reasons:
        return WorkspaceHealth.NOT_DIRECTORY
    return WorkspaceHealth.INVALID


class WorkspaceRegistry:
    """In-memory logical workspace registry with explicit mode boundaries."""

    def __init__(self) -> None:
        self._records: dict[str, WorkspaceRecord] = {}

    def register(self, binding: WorkspaceBinding, *, mode: WorkspaceMode) -> WorkspaceRecord:
        if binding.workspace_id in self._records:
            raise ValueError("workspace_id_already_registered")
        if mode is WorkspaceMode.MANAGED and not binding.owned_or_delegated:
            raise ValueError("managed_workspace_requires_ownership_or_delegation")
        plan = plan_workspace(binding)
        record = WorkspaceRecord(binding, mode, workspace_health(plan), plan.path)
        self._records[binding.workspace_id] = record
        return record

    def get(self, workspace_id: str) -> WorkspaceRecord:
        try:
            return self._records[workspace_id]
        except KeyError as exc:
            raise KeyError("workspace_not_registered") from exc

    def refresh_health(self, workspace_id: str) -> WorkspaceRecord:
        current = self.get(workspace_id)
        plan = plan_workspace(current.binding)
        refreshed = WorkspaceRecord(current.binding, current.mode, workspace_health(plan), plan.path)
        self._records[workspace_id] = refreshed
        return refreshed

    def __len__(self) -> int:
        return len(self._records)
