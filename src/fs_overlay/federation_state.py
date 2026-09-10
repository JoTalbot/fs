"""Durable, auditable federation state built on the existing event journal."""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Protocol

from .event_log import EventLog
from .federation_protocol import FederationEnvelope


class AdmissionCoordinator(Protocol):
    """Minimal coordination boundary used by durable federation admission."""

    def acquire(self, resource_id: str): ...


@dataclass(frozen=True)
class FederationState:
    last_sequence: dict[str, int]
    seen_message_ids: frozenset[str]


class DurableFederationState:
    """Persist already-validated protocol admissions across process restarts.

    Signature, trust and freshness checks belong to ``FederationReceiver`` or
    another admission layer. This class is deliberately the durable state
    boundary, not an authentication mechanism.

    The admission critical section is serialized for threads sharing one
    instance. Multi-process writers require a deployment-specific
    ``AdmissionCoordinator`` or transactional storage implementation. The
    coordinator, when supplied, covers both the admission decision and the
    journal write.
    """

    RESOURCE_ID = "federation-events"

    def __init__(self, path: str | Path, *, coordinator: AdmissionCoordinator | None = None):
        self.events = EventLog(path)
        self.last_sequence: dict[str, int] = {}
        self.seen_message_ids: set[str] = set()
        self._lock = threading.RLock()
        self._coordinator = coordinator
        self._replay()

    def _replay(self) -> None:
        for event in self.events.replay():
            if event.get("event") != "federation.accepted":
                continue
            details = event.get("details")
            if not isinstance(details, dict):
                continue
            sender = details.get("sender_node")
            message_id = details.get("message_id")
            sequence = details.get("sequence")
            if not (isinstance(sender, str) and sender and isinstance(message_id, str) and message_id and isinstance(sequence, int)):
                continue
            if message_id in self.seen_message_ids:
                raise ValueError("duplicate federation message ID in durable state")
            previous = self.last_sequence.get(sender, -1)
            if sequence <= previous:
                raise ValueError("non-increasing federation sequence in durable state")
            self.last_sequence[sender] = sequence
            self.seen_message_ids.add(message_id)

    def accept(self, envelope: FederationEnvelope) -> bool:
        """Durably admit an envelope after external authentication/admission."""
        with self._lock:
            coordination = (
                self._coordinator.acquire(self.RESOURCE_ID)
                if self._coordinator is not None
                else nullcontext()
            )
            with coordination:
                if not envelope.sender_node or not envelope.message_id or envelope.sequence < 0:
                    return False
                if envelope.message_id in self.seen_message_ids:
                    return False
                if envelope.sequence <= self.last_sequence.get(envelope.sender_node, -1):
                    return False
                self.events.emit(
                    "federation.accepted",
                    details={
                        "sender_node": envelope.sender_node,
                        "message_id": envelope.message_id,
                        "message_type": envelope.message_type,
                        "sequence": envelope.sequence,
                        "digest": envelope.digest(),
                    },
                )
                self.last_sequence[envelope.sender_node] = envelope.sequence
                self.seen_message_ids.add(envelope.message_id)
                return True

    def snapshot(self) -> FederationState:
        with self._lock:
            return FederationState(dict(self.last_sequence), frozenset(self.seen_message_ids))
