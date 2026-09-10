"""Audit trail for federation decisions and authorized replica outcomes."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .event_log import EventLog
from .federation_control import ReconciliationDecision
from .replication import ReplicaResult


class FederationAuditTrail:
    """Record federation control decisions without executing them."""

    def __init__(self, path: str | Path):
        self.log = EventLog(path)

    def record_decisions(self, decisions: Iterable[ReconciliationDecision]) -> tuple[dict[str, object], ...]:
        records = []
        for decision in decisions:
            records.append(self.log.emit(
                "federation.reconciliation_decision",
                object_id=decision.object_id,
                details={
                    "source_node": decision.source_node,
                    "target_node": decision.target_node,
                    "action": decision.action,
                    "reason": decision.reason,
                },
            ))
        return tuple(records)

    def record_result(self, result: ReplicaResult, *, causal_parent: str | None = None) -> dict[str, object]:
        return self.log.emit(
            "federation.replica_result",
            object_id=result.action.object_id,
            causal_parent=causal_parent,
            details={
                "source_node": result.action.source_node,
                "target_node": result.action.target_node,
                "expected_sha256": result.action.expected_sha256,
                "status": result.status,
                "observed_sha256": result.observed_sha256,
                "reason": result.reason,
            },
        )
