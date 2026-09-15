"""Non-destructive contract for future workspace transfer materialization.

This module validates that an explicit authority grant and durable journal state
match the exact transfer plan. It intentionally performs no filesystem mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .authority_revocation import AuthorityRevocationRegistry
from .workspace_migration import WorkspaceTransfer, WorkspaceTransferPlan
from .workspace_transfer_authority import TransferAuthority, TransferAuthorityScope
from .workspace_transfer_journal import (
    TransferJournalPhase,
    WorkspaceTransferJournal,
)


@dataclass(frozen=True, slots=True)
class MaterializationPreflight:
    """Evidence that a future materializer may enter its own mutation boundary."""

    transaction_id: str
    snapshot_id: str
    source_workspace_id: str
    destination_workspace_id: str
    operation: WorkspaceTransfer
    source_preserved: bool = True


class WorkspaceMaterializer(Protocol):
    """Interface for a future authority-bearing transfer executor.

    Implementations must revalidate preconditions immediately before mutation,
    journal each durable phase, preserve the source by default, and provide
    crash/rollback evidence. This protocol itself grants no filesystem access.
    """

    def prepare(
        self,
        plan: WorkspaceTransferPlan,
        authority: TransferAuthority,
        journal: WorkspaceTransferJournal,
    ) -> MaterializationPreflight: ...


def validate_materialization_preflight(
    plan: WorkspaceTransferPlan,
    authority: TransferAuthority,
    journal: WorkspaceTransferJournal,
    revocations: AuthorityRevocationRegistry | None = None,
) -> MaterializationPreflight:
    """Validate exact plan/authority/journal binding without touching the host FS."""
    if not plan.ready:
        raise ValueError("materialization requires a ready transfer plan")
    if not isinstance(authority, TransferAuthority):
        raise PermissionError("materialization requires an issued transfer authority")
    if authority.scope is not TransferAuthorityScope.MATERIALIZE:
        raise PermissionError("materialization requires materialize authority")
    if plan.operation is WorkspaceTransfer.EXPORT:
        raise ValueError("materialization requires an import or migration plan")
    if not plan.destination_path or not plan.destination_workspace_id:
        raise ValueError("materialization requires a destination workspace")
    if not authority.source_preserved:
        raise PermissionError("materialization authority must preserve the source")
    if (
        authority.snapshot_id != plan.snapshot_id
        or authority.source_workspace_id != plan.source_workspace_id
        or authority.destination_workspace_id != plan.destination_workspace_id
    ):
        raise PermissionError("authority does not match transfer plan")
    if revocations is not None:
        if not authority.authority_id:
            raise PermissionError("revocation check requires authority provenance")
        if revocations.is_revoked(authority.authority_id):
            raise PermissionError("transfer authority has been revoked")

    entries = list(journal.replay())
    current = next(
        (entry for entry in reversed(entries) if entry.transaction_id == authority.transaction_id),
        None,
    )
    if current is None:
        raise ValueError("journal transaction does not exist")
    if current.operation is not plan.operation or current.snapshot_id != plan.snapshot_id:
        raise PermissionError("journal transaction does not match transfer plan")
    if (
        current.source_workspace_id != plan.source_workspace_id
        or current.destination_workspace_id != plan.destination_workspace_id
    ):
        raise PermissionError("journal workspaces do not match transfer plan")
    if current.phase not in {
        TransferJournalPhase.PREPARED,
        TransferJournalPhase.MATERIALIZING,
    }:
        raise ValueError("transfer is not in a materializable journal state")

    return MaterializationPreflight(
        transaction_id=authority.transaction_id,
        snapshot_id=plan.snapshot_id,
        source_workspace_id=plan.source_workspace_id,
        destination_workspace_id=plan.destination_workspace_id,
        operation=plan.operation,
        source_preserved=plan.source_preserved,
    )
