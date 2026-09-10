"""Durable, auditable federation state built on the existing event journal."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .event_log import EventLog
from .federation_protocol import FederationEnvelope


@dataclass(frozen=True)
class FederationState:
    last_sequence: dict[str, int]
    seen_message_ids: frozenset[str]


class DurableFederationState:
    """Persist accepted protocol state without coupling it to network transport."""

    def __init__(self, path: str | Path):
        self.events = EventLog(path)
        self.last_sequence: dict[str, int] = {}
        self.seen_message_ids: set[str] = set()
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
            if isinstance(sender, str) and isinstance(message_id, str) and isinstance(sequence, int):
                self.last_sequence[sender] = max(self.last_sequence.get(sender, -1), sequence)
                self.seen_message_ids.add(message_id)

    def accept(self, envelope: FederationEnvelope) -> bool:
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
        return FederationState(dict(self.last_sequence), frozenset(self.seen_message_ids))
