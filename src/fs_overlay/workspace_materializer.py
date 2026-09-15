"""Non-destructive materializer protocol for workspace transfers.

The protocol binds a transfer plan to explicit authority and durable journal state,
but deliberately does not write, replace, delete, chmod, mount, or otherwise
mutate host filesystem state. A future executor must provide its own crash-safe
filesystem transaction and evidence boundary.
"""
from __future__ import annotations

from dataclasses import dataclass

from .workspace_transfer_authority import TransferAuthority, TransferAuthorityScope
from .workspace_transfer_journal import (
    TransferJournalPhase,
    WorkspaceTransferJournal,
)
from .workspace_migration import WorkspaceTransferPlan


@dataclass(frozen=True, slots=True)
class MaterializationContext:
    """Validated inputs for one future filesystem materialization transaction."""

    authority: TransferAuthority
    plan: WorkspaceTransferPlan
    transaction_id: str


class MaterializationRejected(PermissionError):
    """Raised when materialization prerequisites do not match exactly."""


def validate_materialization_context(
    authority: TransferAuthority,
    plan: WorkspaceTransferPlan,
    journal: WorkspaceTransferJournal,
) -> MaterializationContext:
    """Validate authority and journal identity without touching the host FS."""
    if authority.scope is not TransferAuthorityScope.MATERIALIZE:
        raise MaterializationRejected("materialization requires MATERIALIZE authority")
    if not plan.ready:
        raise MaterializationRejected("materialization requires a ready transfer plan")
    if authority.transaction_id == "":
        raise MaterializationRejected("materialization requires a transaction id")
    if authority.snapshot_id != plan.snapshot_id:
        raise MaterializationRejected("authority snapshot does not match transfer plan")
    if authority.source_workspace_id != plan.source_workspace_id:
        raise MaterializationRejected("authority source does not match transfer plan")
    if authority.destination_workspace_id != plan.destination_workspace_id:
        raise MaterializationRejected("authority destination does not match transfer plan")
    entries = [
        entry
        for entry in journal.replay()
        if entry.transaction_id == authority.transaction_id
    ]
    if not entries:
        raise MaterializationRejected("materialization transaction is not journaled")
    current = entries[-1]
    if current.phase not in {
        TransferJournalPhase.PREPARED,
        TransferJournalPhase.MATERIALIZING,
    }:
        raise MaterializationRejected("materialization transaction is already terminal")
    if (
        current.operation != plan.operation
        or current.snapshot_id != plan.snapshot_id
        or current.source_workspace_id != plan.source_workspace_id
        or current.destination_workspace_id != plan.destination_workspace_id
    ):
        raise MaterializationRejected("journal transaction does not match transfer plan")
    return MaterializationContext(authority, plan, authority.transaction_id)


class WorkspaceMaterializer:
    """Protocol adapter that advances intent, never filesystem state."""

    def __init__(self, journal: WorkspaceTransferJournal):
        self.journal = journal

    def prepare(self, context: MaterializationContext) -> None:
        """Enter materializing state; no host filesystem operation is performed."""
        current = validate_materialization_context(
            context.authority, context.plan, self.journal
        )
        entries = [
            entry
            for entry in self.journal.replay()
            if entry.transaction_id == current.transaction_id
        ]
        if entries[-1].phase is TransferJournalPhase.PREPARED:
            self.journal.mark(
                current.transaction_id,
                current.plan,
                TransferJournalPhase.MATERIALIZING,
            )

    def commit(self, context: MaterializationContext) -> None:
        """Refuse to claim filesystem commit; only a future executor may do so."""
        raise NotImplementedError(
            "filesystem commit requires a separately qualified crash-safe executor"
        )

    def abort(self, context: MaterializationContext) -> None:
        """Record an explicit abort intent without touching host filesystem state."""
        current = validate_materialization_context(
            context.authority, context.plan, self.journal
        )
        self.journal.mark(
            current.transaction_id,
            current.plan,
            TransferJournalPhase.ABORTED,
        )
