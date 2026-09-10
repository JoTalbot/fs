"""Transport-neutral federation envelopes with replay protection.

This module defines protocol semantics only. It does not provide networking,
cryptographic signing, or implicit peer discovery. Production deployments must
inject an audited signer/verifier and a transport adapter.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Callable


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


@dataclass(frozen=True)
class FederationEnvelope:
    sender_node: str
    message_id: str
    message_type: str
    sequence: int
    issued_ns: int
    payload: dict[str, object]
    signature: bytes | None = None

    def unsigned_bytes(self) -> bytes:
        return _canonical({
            "sender_node": self.sender_node,
            "message_id": self.message_id,
            "message_type": self.message_type,
            "sequence": self.sequence,
            "issued_ns": self.issued_ns,
            "payload": self.payload,
        })

    def digest(self) -> str:
        return hashlib.sha256(self.unsigned_bytes()).hexdigest()

    def verify(self, verifier: Callable[[bytes, bytes, str], bool] | None) -> bool:
        if verifier is None or self.signature is None:
            return False
        return verifier(self.unsigned_bytes(), self.signature, self.sender_node)


class ReplayGuard:
    """Reject duplicate, reordered, or stale envelopes per sender."""

    def __init__(self) -> None:
        self._last_sequence: dict[str, int] = {}
        self._seen_ids: set[str] = set()

    def accept(self, envelope: FederationEnvelope, *, now_ns: int | None = None,
               max_age_ns: int = 300_000_000_000) -> bool:
        if not envelope.sender_node or not envelope.message_id or envelope.sequence < 0:
            return False
        if envelope.message_id in self._seen_ids:
            return False
        now = time.time_ns() if now_ns is None else now_ns
        if envelope.issued_ns > now or now - envelope.issued_ns > max_age_ns:
            return False
        previous = self._last_sequence.get(envelope.sender_node, -1)
        if envelope.sequence <= previous:
            return False
        self._last_sequence[envelope.sender_node] = envelope.sequence
        self._seen_ids.add(envelope.message_id)
        return True


class FederationReceiver:
    """Validate signature and freshness before handing payload to an adapter."""

    def __init__(self, verifier: Callable[[bytes, bytes, str], bool], replay_guard: ReplayGuard | None = None):
        self.verifier = verifier
        self.replay_guard = replay_guard or ReplayGuard()

    def receive(self, envelope: FederationEnvelope, *, now_ns: int | None = None) -> dict[str, object] | None:
        if not envelope.verify(self.verifier):
            return None
        if not self.replay_guard.accept(envelope, now_ns=now_ns):
            return None
        return dict(envelope.payload)
