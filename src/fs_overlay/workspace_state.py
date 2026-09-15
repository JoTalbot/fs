"""Content-addressed logical state for registered FS workspaces.

A workspace snapshot records the storage inventory visible to the FS control
plane. It does not copy, mount, delete, or otherwise mutate the host path.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .storage_engine import LocalStorageEngine
from .storage_resilience import Snapshot, SnapshotStore
from .workspace import WorkspaceBinding, plan_workspace
from .workspace_registry import WorkspaceRegistry


@dataclass(frozen=True, slots=True)
class WorkspaceState:
    """Verified association between a logical workspace and a snapshot."""

    workspace_id: str
    snapshot: Snapshot

    def validate(self) -> tuple[str, ...]:
        metadata = self.snapshot.metadata or {}
        reasons: list[str] = []
        if metadata.get("workspace_id") != self.workspace_id:
            reasons.append("snapshot_workspace_mismatch")
        return tuple(reasons)


class WorkspaceStateStore:
    """Create and retrieve immutable workspace-scoped snapshot state."""

    def __init__(self, root: str | Path):
        self.store = SnapshotStore(root)

    def create(
        self,
        binding: WorkspaceBinding,
        engine: LocalStorageEngine,
        *,
        generation: int = 0,
        metadata: dict[str, str] | None = None,
    ) -> WorkspaceState:
        plan = plan_workspace(binding)
        if not plan.admitted:
            raise ValueError(f"workspace_not_admitted: {','.join(plan.reasons)}")
        if generation < 0:
            raise ValueError("generation must be non-negative")
        snapshot_metadata = dict(metadata or {})
        existing = snapshot_metadata.get("workspace_id")
        if existing is not None and existing != binding.workspace_id:
            raise ValueError("snapshot_workspace_mismatch")
        snapshot_metadata["workspace_id"] = binding.workspace_id
        snapshot_metadata["workspace_mode"] = "managed" if binding.owned_or_delegated else "observed"
        snapshot = self.store.create(
            engine.inventory.records.keys(), generation=generation, metadata=snapshot_metadata
        )
        return WorkspaceState(binding.workspace_id, snapshot)

    def create_registered(
        self,
        registry: WorkspaceRegistry,
        workspace_id: str,
        engine: LocalStorageEngine,
        *,
        generation: int = 0,
        metadata: dict[str, str] | None = None,
    ) -> WorkspaceState:
        record = registry.get(workspace_id)
        return self.create(record.binding, engine, generation=generation, metadata=metadata)

    def get(self, workspace_id: str, snapshot_id: str) -> WorkspaceState:
        state = WorkspaceState(workspace_id, self.store.get(snapshot_id))
        reasons = state.validate()
        if reasons:
            raise ValueError(",".join(reasons))
        return state
