"""Plan-only workspace migration, import, and export boundaries.

These APIs describe safe state movement but never perform host filesystem
mutation. Execution remains a separate, authority-bearing operation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .workspace import WorkspaceBinding, WorkspacePlan, plan_workspace
from .workspace_state import WorkspaceState, WorkspaceStateStore
from .workspace_registry import WorkspaceMode, WorkspaceRecord, WorkspaceRegistry


class WorkspaceTransfer(str, Enum):
    EXPORT = "export"
    IMPORT = "import"
    MIGRATE = "migrate"


@dataclass(frozen=True, slots=True)
class WorkspaceTransferPlan:
    """Verified, non-destructive transfer intent.

    ``source_preserved`` is always true at the planning layer. A future
    destructive move must be a distinct, explicitly authorized operation.
    """

    operation: WorkspaceTransfer
    snapshot_id: str
    source_workspace_id: str
    destination_workspace_id: str | None
    source_path: Path | None
    destination_path: Path | None
    source_preserved: bool = True
    destination_must_be_verified: bool = True
    reasons: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return not self.reasons


def plan_export(
    state: WorkspaceState,
    source: WorkspaceBinding,
) -> WorkspaceTransferPlan:
    """Plan a non-destructive export of verified workspace state."""
    reasons = list(state.validate())
    source_plan = plan_workspace(source)
    reasons.extend(source_plan.reasons)
    if source.workspace_id != state.workspace_id:
        reasons.append("source_workspace_mismatch")
    return WorkspaceTransferPlan(
        WorkspaceTransfer.EXPORT,
        state.snapshot.snapshot_id,
        state.workspace_id,
        None,
        Path(source.host_path),
        None,
        reasons=tuple(dict.fromkeys(reasons)),
    )


def plan_import(
    state: WorkspaceState,
    destination: WorkspaceBinding,
) -> WorkspaceTransferPlan:
    """Plan import only into an existing, explicitly managed destination."""
    reasons = list(state.validate())
    destination_plan = plan_workspace(destination)
    reasons.extend(destination_plan.reasons)
    if not destination.owned_or_delegated:
        reasons.append("import_destination_requires_ownership_or_delegation")
    if destination.read_only:
        reasons.append("import_destination_must_be_writable")
    return WorkspaceTransferPlan(
        WorkspaceTransfer.IMPORT,
        state.snapshot.snapshot_id,
        state.workspace_id,
        destination.workspace_id,
        None,
        Path(destination.host_path),
        reasons=tuple(dict.fromkeys(reasons)),
    )


def plan_migration(
    state: WorkspaceState,
    source: WorkspaceBinding,
    destination: WorkspaceBinding,
) -> WorkspaceTransferPlan:
    """Plan export-then-import while preserving the source workspace."""
    export = plan_export(state, source)
    import_plan = plan_import(state, destination)
    reasons = list(export.reasons) + list(import_plan.reasons)
    if source.workspace_id == destination.workspace_id:
        reasons.append("migration_requires_distinct_source_and_destination")
    return WorkspaceTransferPlan(
        WorkspaceTransfer.MIGRATE,
        state.snapshot.snapshot_id,
        source.workspace_id,
        destination.workspace_id,
        Path(source.host_path),
        Path(destination.host_path),
        reasons=tuple(dict.fromkeys(reasons)),
    )


def plan_registered_migration(
    registry: WorkspaceRegistry,
    state_store: WorkspaceStateStore,
    snapshot_workspace_id: str,
    snapshot_id: str,
    destination_workspace_id: str,
) -> WorkspaceTransferPlan:
    """Resolve both bindings from the registry before planning migration."""
    state = state_store.get(snapshot_workspace_id, snapshot_id)
    source: WorkspaceRecord = registry.get(snapshot_workspace_id)
    destination: WorkspaceRecord = registry.get(destination_workspace_id)
    if destination.mode is not WorkspaceMode.MANAGED:
        return WorkspaceTransferPlan(
            WorkspaceTransfer.MIGRATE,
            snapshot_id,
            source.binding.workspace_id,
            destination.binding.workspace_id,
            Path(source.binding.host_path),
            Path(destination.binding.host_path),
            reasons=("migration_destination_must_be_managed",),
        )
    return plan_migration(state, source.binding, destination.binding)
