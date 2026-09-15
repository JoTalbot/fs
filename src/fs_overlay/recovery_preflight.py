"""Fail-closed preflight for crash recovery decisions.

Recovery is a separate path from normal executor admission because a recovery
candidate is already MATERIALIZING, while a new executor transaction must be
PREPARED. This module requires an independently qualified evidence verifier;
reconciliation alone is never treated as proof of host state.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .workspace_transfer_journal import TransferJournalEntry, TransferJournalPhase
from .workspace_transfer_recovery import (
    TransferRecoveryEvidence,
    TransferRecoveryPlan,
    reconcile_materializing_transaction,
    recovery_evidence_digest,
)


class RecoveryEvidenceVerifier(Protocol):
    """Provider that independently verifies externally observed recovery evidence."""

    def verify(
        self,
        transaction: TransferJournalEntry,
        evidence: TransferRecoveryEvidence,
    ) -> bool:
        """Return true only when evidence was independently authenticated/verified."""


@dataclass(frozen=True, slots=True)
class RecoveryPreflightResult:
    """Verified recovery decision plus the exact evidence digest; no capability."""

    transaction: TransferJournalEntry
    evidence: TransferRecoveryEvidence
    plan: TransferRecoveryPlan
    evidence_digest: str


def recovery_preflight(
    transaction: TransferJournalEntry,
    evidence: TransferRecoveryEvidence,
    *,
    evidence_verifier: RecoveryEvidenceVerifier,
) -> RecoveryPreflightResult:
    """Require independently verified evidence before accepting reconciliation."""
    if transaction.phase is not TransferJournalPhase.MATERIALIZING:
        raise PermissionError("recovery preflight requires a materializing transaction")
    if evidence.transaction_id != transaction.transaction_id:
        raise PermissionError("recovery evidence transaction does not match journal")
    if evidence.snapshot_id != transaction.snapshot_id:
        raise PermissionError("recovery evidence snapshot does not match journal")

    try:
        verified = evidence_verifier.verify(transaction, evidence)
    except Exception as exc:
        raise PermissionError("recovery evidence verification failed") from exc
    if verified is not True:
        raise PermissionError("recovery evidence is not independently verified")

    plan = reconcile_materializing_transaction(transaction, evidence)
    if plan.operation is not transaction.operation:
        raise PermissionError("recovery plan operation does not match journal")
    return RecoveryPreflightResult(
        transaction,
        evidence,
        plan,
        recovery_evidence_digest(evidence),
    )
