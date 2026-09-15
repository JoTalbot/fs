"""Plan-only crash reconciliation for workspace transfer transactions.

Recovery is evidence-driven and fail-closed. This module never inspects or
mutates the host filesystem itself, never marks a transaction committed, and
never grants authority. A future executor must obtain independent evidence
before applying any recovery decision.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum

from .workspace_migration import WorkspaceTransfer
from .workspace_transfer_journal import TransferJournalEntry, TransferJournalPhase


class DestinationRecoveryState(str, Enum):
    """Externally supplied observation of a transfer destination."""

    ABSENT = "absent"
    MATCHES_SNAPSHOT = "matches_snapshot"
    CONFLICTING = "conflicting"
    UNKNOWN = "unknown"


class RecoveryDecision(str, Enum):
    """Safe reconciliation outcomes; none performs a filesystem operation."""

    ABORT_PROVEN = "abort_proven"
    COMMIT_PROVEN = "commit_proven"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True, slots=True)
class TransferRecoveryEvidence:
    """Evidence reported by a separately qualified destination observer."""

    transaction_id: str
    snapshot_id: str
    destination_state: DestinationRecoveryState
    destination_verified: bool
    mutation_complete: bool
    source_preserved: bool
    rollback_safe: bool
    staging_absent: bool = False


@dataclass(frozen=True, slots=True)
class TransferRecoveryPlan:
    """Non-destructive reconciliation decision for one journal candidate."""

    transaction_id: str
    operation: WorkspaceTransfer
    snapshot_id: str
    decision: RecoveryDecision
    reason: str


def recovery_evidence_digest(evidence: TransferRecoveryEvidence) -> str:
    """Return a deterministic SHA-256 digest of the complete recovery evidence.

    The digest deliberately covers every evidence field so an audit event binds
    to the exact evidence that was independently verified, rather than merely to
    the later reconciliation decision.
    """
    payload = {
        "transaction_id": evidence.transaction_id,
        "snapshot_id": evidence.snapshot_id,
        "destination_state": evidence.destination_state.value,
        "destination_verified": evidence.destination_verified,
        "mutation_complete": evidence.mutation_complete,
        "source_preserved": evidence.source_preserved,
        "rollback_safe": evidence.rollback_safe,
        "staging_absent": evidence.staging_absent,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def reconcile_materializing_transaction(
    entry: TransferJournalEntry,
    evidence: TransferRecoveryEvidence,
) -> TransferRecoveryPlan:
    """Reconcile one crashed MATERIALIZING transaction from explicit evidence.

    The function is deliberately conservative: unknown, conflicting, incomplete,
    or source-destructive evidence becomes manual review rather than an automatic
    commit or rollback. The caller remains responsible for authorization and for
    recording any eventual state transition in the durable journal.
    """
    if entry.phase is not TransferJournalPhase.MATERIALIZING:
        raise ValueError("reconciliation requires a materializing journal entry")
    if evidence.transaction_id != entry.transaction_id:
        raise ValueError("recovery evidence transaction mismatch")
    if evidence.snapshot_id != entry.snapshot_id:
        raise ValueError("recovery evidence snapshot mismatch")
    if not evidence.source_preserved:
        raise PermissionError("recovery requires preserved source evidence")

    if (
        evidence.destination_state is DestinationRecoveryState.MATCHES_SNAPSHOT
        and evidence.destination_verified
        and evidence.mutation_complete
        and evidence.staging_absent
    ):
        return TransferRecoveryPlan(
            entry.transaction_id,
            entry.operation,
            entry.snapshot_id,
            RecoveryDecision.COMMIT_PROVEN,
            "destination matches snapshot, mutation completion is evidenced, and staging is absent",
        )

    if evidence.destination_state is DestinationRecoveryState.ABSENT:
        if evidence.mutation_complete:
            return TransferRecoveryPlan(
                entry.transaction_id,
                entry.operation,
                entry.snapshot_id,
                RecoveryDecision.MANUAL_REVIEW,
                "destination is absent but mutation completion conflicts with rollback proof",
            )
        if evidence.rollback_safe and evidence.staging_absent:
            return TransferRecoveryPlan(
                entry.transaction_id,
                entry.operation,
                entry.snapshot_id,
                RecoveryDecision.ABORT_PROVEN,
                "destination is absent, staging is absent, and rollback safety is independently evidenced",
            )
        return TransferRecoveryPlan(
            entry.transaction_id,
            entry.operation,
            entry.snapshot_id,
            RecoveryDecision.MANUAL_REVIEW,
            "destination is absent but rollback safety or staging absence is not evidenced",
        )

    return TransferRecoveryPlan(
        entry.transaction_id,
        entry.operation,
        entry.snapshot_id,
        RecoveryDecision.MANUAL_REVIEW,
        "recovery evidence is incomplete, conflicting, or leaves residual staging state",
    )
