"""Fail-closed rollback evidence contract for workspace transfers.

This module only classifies independently supplied evidence. It never deletes,
restores, replaces, or otherwise mutates the host filesystem.
"""
from __future__ import annotations

from dataclasses import dataclass

from .workspace_transfer_journal import TransferJournalEntry, TransferJournalPhase


@dataclass(frozen=True, slots=True)
class TransferRollbackEvidence:
    """Evidence supplied by a separately qualified recovery observer."""

    transaction_id: str
    snapshot_id: str
    destination_absent: bool
    staging_absent: bool
    source_preserved: bool
    rollback_verified: bool


@dataclass(frozen=True, slots=True)
class TransferRollbackPlan:
    """Non-destructive rollback classification for one interrupted transfer."""

    transaction_id: str
    snapshot_id: str
    proven: bool
    reason: str


def validate_rollback_evidence(
    entry: TransferJournalEntry,
    evidence: TransferRollbackEvidence,
) -> TransferRollbackPlan:
    """Prove rollback safety only from complete, identity-matched evidence."""
    if entry.phase is not TransferJournalPhase.MATERIALIZING:
        raise ValueError("rollback evidence requires a materializing journal entry")
    if evidence.transaction_id != entry.transaction_id:
        raise ValueError("rollback evidence transaction mismatch")
    if evidence.snapshot_id != entry.snapshot_id:
        raise ValueError("rollback evidence snapshot mismatch")
    if not evidence.source_preserved:
        raise PermissionError("rollback requires preserved source evidence")

    proven = (
        evidence.destination_absent
        and evidence.staging_absent
        and evidence.rollback_verified
    )
    if proven:
        reason = "destination and staging are absent and rollback is independently verified"
    else:
        reason = "rollback evidence is incomplete or residual state remains"
    return TransferRollbackPlan(
        entry.transaction_id,
        entry.snapshot_id,
        proven,
        reason,
    )
