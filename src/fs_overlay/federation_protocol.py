"""Transport-neutral federation envelopes with replay protection."""
from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
from dataclasses import dataclass
from typing import Callable


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _reject_duplicate_object_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("federation envelope contains duplicate JSON fields")
        result[key] = value
    return result


def _validate_non_negative_int(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"invalid federation envelope {field}")
    return value


def _validate_non_empty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"invalid federation envelope {field}")
    return value


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

    def to_bytes(self) -> bytes:
        value = {
            "sender_node": self.sender_node,
            "message_id": self.message_id,
            "message_type": self.message_type,
            "sequence": self.sequence,
            "issued_ns": self.issued_ns,
            "payload": self.payload,
            "signature": base64.b64encode(self.signature).decode("ascii") if self.signature is not None else None,
        }
        return _canonical(value)

    @classmethod
    def from_bytes(cls, data: bytes) -> "FederationEnvelope":
        try:
            value = json.loads(data.decode("utf-8"), object_pairs_hook=_reject_duplicate_object_keys)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError("invalid federation envelope JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("federation envelope must be an object")
        expected_fields = {
            "sender_node", "message_id", "message_type", "sequence",
            "issued_ns", "payload", "signature",
        }
        if set(value) != expected_fields:
            raise ValueError("federation envelope fields are invalid")

        sender_node = _validate_non_empty_string(value["sender_node"], "sender_node")
        message_id = _validate_non_empty_string(value["message_id"], "message_id")
        message_type = _validate_non_empty_string(value["message_type"], "message_type")
        sequence = _validate_non_negative_int(value["sequence"], "sequence")
        issued_ns = _validate_non_negative_int(value["issued_ns"], "issued_ns")
        payload = value["payload"]
        if not isinstance(payload, dict):
            raise ValueError("federation payload must be an object")

        signature = value["signature"]
        if signature is None:
            decoded = None
        elif isinstance(signature, str):
            try:
                decoded = base64.b64decode(signature, validate=True)
            except (ValueError, TypeError) as exc:
                raise ValueError("invalid federation envelope signature") from exc
        else:
            raise ValueError("invalid federation envelope signature")

        return cls(sender_node, message_id, message_type, sequence, issued_ns, payload, decoded)


class ReplayGuard:
    """Reject duplicate, reordered, or stale envelopes per sender.

    Admission is atomic within one process so concurrent receiver threads cannot
    both observe the same message ID or sequence as unused before either records it.
    Cross-process durability remains the responsibility of ``DurableFederationState``.
    """

    def __init__(self) -> None:
        self._last_sequence: dict[str, int] = {}
        self._seen_ids: set[str] = set()
        self._lock = threading.Lock()

    def accept(self, envelope: FederationEnvelope, *, now_ns: int | None = None,
               max_age_ns: int = 300_000_000_000) -> bool:
        if not envelope.sender_node or not envelope.message_id or envelope.sequence < 0:
            return False
        now = time.time_ns() if now_ns is None else now_ns
        if envelope.issued_ns > now or now - envelope.issued_ns > max_age_ns:
            return False
        with self._lock:
            if envelope.message_id in self._seen_ids:
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
