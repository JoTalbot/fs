"""Append-only audit trail for workspace transfer recovery decisions.

Audit records document a recovery decision; they never authorize, apply, or
prove a filesystem transition. The chain is fail-closed so tampering or
reordering cannot silently become trusted recovery history.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path

from .durable_coordination import FileAdmissionCoordinator
from .recovery_preflight import RecoveryPreflightResult
from .workspace_migration import WorkspaceTransfer
from .workspace_transfer_journal import TransferJournalPhase
from .workspace_transfer_recovery import RecoveryDecision, recovery_evidence_digest


class RecoveryAuditTransition(str, Enum):
    """Proposed journal transition represented by an audit event."""

    NONE = "none"
    COMMIT = "commit"
    ABORT = "abort"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True, slots=True)
class RecoveryAuditEvent:
    """Immutable record of a recovery decision, not an authorization."""

    sequence: int
    transaction_id: str
    snapshot_id: str
    operation: WorkspaceTransfer
    phase_before: TransferJournalPhase
    decision: RecoveryDecision
    proposed_transition: RecoveryAuditTransition
    reason: str
    evidence_digest: str
    previous_digest: str | None
    event_digest: str

    def as_record(self) -> dict[str, object]:
        return {
            "version": 1,
            "sequence": self.sequence,
            "transaction_id": self.transaction_id,
            "snapshot_id": self.snapshot_id,
            "operation": self.operation.value,
            "phase_before": self.phase_before.value,
            "decision": self.decision.value,
            "proposed_transition": self.proposed_transition.value,
            "reason": self.reason,
            "evidence_digest": self.evidence_digest,
            "previous_digest": self.previous_digest,
            "event_digest": self.event_digest,
        }


class RecoveryAuditCorruption(ValueError):
    """Raised when recovery audit history cannot be trusted."""


def _canonical(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def _event_digest(event: RecoveryAuditEvent) -> str:
    payload = event.as_record().copy()
    payload["event_digest"] = None
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _transition(decision: RecoveryDecision) -> RecoveryAuditTransition:
    return {
        RecoveryDecision.COMMIT_PROVEN: RecoveryAuditTransition.COMMIT,
        RecoveryDecision.ABORT_PROVEN: RecoveryAuditTransition.ABORT,
        RecoveryDecision.MANUAL_REVIEW: RecoveryAuditTransition.MANUAL_REVIEW,
    }[decision]


def _valid_digest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


class RecoveryAuditLog:
    """Durable, append-only recovery decision log with hash-chain replay.

    Appends require a :class:`RecoveryPreflightResult`, so the audit event is
    bound to the exact evidence digest calculated after independent evidence
    verification. A reconciliation plan alone is intentionally insufficient.

    Every append serializes replay, sequence allocation, hash-chain linkage,
    and the durable write under the same cross-process lock. Replay itself is
    deliberately lock-free so readers never hold the writer lock while doing
    potentially long validation.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._coordinator = FileAdmissionCoordinator(
            self.path.parent / ".recovery-audit-locks"
        )

    def append(
        self,
        result: RecoveryPreflightResult,
        phase_before: TransferJournalPhase,
    ) -> RecoveryAuditEvent:
        """Append a recovery decision only after verified evidence preflight."""
        if phase_before is not TransferJournalPhase.MATERIALIZING:
            raise ValueError("recovery audit requires a materializing phase")
        if result.transaction.phase is not TransferJournalPhase.MATERIALIZING:
            raise ValueError("recovery audit requires a materializing transaction")
        if result.plan.transaction_id != result.transaction.transaction_id:
            raise ValueError("recovery audit result transaction mismatch")
        if result.plan.snapshot_id != result.transaction.snapshot_id:
            raise ValueError("recovery audit result snapshot mismatch")
        expected_evidence_digest = result.evidence_digest
        if expected_evidence_digest != recovery_evidence_digest(result.evidence):
            raise ValueError("recovery audit evidence digest mismatch")
        if not _valid_digest(expected_evidence_digest):
            raise ValueError("recovery audit requires a SHA-256 evidence digest")
        with self._coordinator.acquire(f"recovery-audit:{self.path.resolve()}"):
            events = tuple(self.replay())
            previous = events[-1] if events else None
            event = RecoveryAuditEvent(
                sequence=previous.sequence + 1 if previous else 1,
                transaction_id=result.transaction.transaction_id,
                snapshot_id=result.transaction.snapshot_id,
                operation=result.plan.operation,
                phase_before=phase_before,
                decision=result.plan.decision,
                proposed_transition=_transition(result.plan.decision),
                reason=result.plan.reason,
                evidence_digest=expected_evidence_digest,
                previous_digest=previous.event_digest if previous else None,
                event_digest="",
            )
            event = replace(event, event_digest=_event_digest(event))
            self._append(event)
            return event

    def replay(self) -> tuple[RecoveryAuditEvent, ...]:
        if not self.path.exists():
            return ()
        result: list[RecoveryAuditEvent] = []
        with self.path.open("rb") as handle:
            for raw_line in handle:
                if not raw_line.endswith(b"\n"):
                    raise RecoveryAuditCorruption("audit contains an incomplete record")
                try:
                    raw = json.loads(raw_line[:-1])
                    event = RecoveryAuditEvent(
                        int(raw["sequence"]),
                        str(raw["transaction_id"]),
                        str(raw["snapshot_id"]),
                        WorkspaceTransfer(str(raw["operation"])),
                        TransferJournalPhase(str(raw["phase_before"])),
                        RecoveryDecision(str(raw["decision"])),
                        RecoveryAuditTransition(str(raw["proposed_transition"])),
                        str(raw["reason"]),
                        str(raw["evidence_digest"]),
                        None if raw.get("previous_digest") is None else str(raw["previous_digest"]),
                        str(raw["event_digest"]),
                    )
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise RecoveryAuditCorruption("audit record is invalid") from exc
                if raw.get("version") != 1:
                    raise RecoveryAuditCorruption("unsupported audit version")
                if event.phase_before is not TransferJournalPhase.MATERIALIZING:
                    raise RecoveryAuditCorruption("audit event is not tied to materializing recovery")
                if not _valid_digest(event.evidence_digest):
                    raise RecoveryAuditCorruption("audit evidence digest is not valid SHA-256")
                if event.previous_digest is not None and not _valid_digest(event.previous_digest):
                    raise RecoveryAuditCorruption("audit previous digest is not valid SHA-256")
                if not _valid_digest(event.event_digest):
                    raise RecoveryAuditCorruption("audit event digest is not valid SHA-256")
                if event.proposed_transition is RecoveryAuditTransition.COMMIT and event.decision is not RecoveryDecision.COMMIT_PROVEN:
                    raise RecoveryAuditCorruption("audit transition conflicts with decision")
                if event.proposed_transition is RecoveryAuditTransition.ABORT and event.decision is not RecoveryDecision.ABORT_PROVEN:
                    raise RecoveryAuditCorruption("audit transition conflicts with decision")
                if event.proposed_transition is RecoveryAuditTransition.MANUAL_REVIEW and event.decision is not RecoveryDecision.MANUAL_REVIEW:
                    raise RecoveryAuditCorruption("audit transition conflicts with decision")
                if event.sequence != len(result) + 1:
                    raise RecoveryAuditCorruption("audit sequence is discontinuous")
                expected_previous = result[-1].event_digest if result else None
                if event.previous_digest != expected_previous:
                    raise RecoveryAuditCorruption("audit hash chain is broken")
                if event.event_digest != _event_digest(event):
                    raise RecoveryAuditCorruption("audit event digest mismatch")
                result.append(event)
        return tuple(result)

    def _append(self, event: RecoveryAuditEvent) -> None:
        encoded = json.dumps(event.as_record(), sort_keys=True, separators=(",", ":")).encode()
        with self.path.open("ab") as handle:
            handle.write(encoded + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
