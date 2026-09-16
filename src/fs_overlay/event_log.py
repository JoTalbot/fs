"""Structured append-only event records for storage and control operations."""
from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Iterator

from .storage_engine import AppendJournal, FORMAT_VERSION, _canonical


class EventLog:
    """Event facade with explicit sequence, monotonic timestamp and causal parent."""

    _EVENT_FIELDS = frozenset({
        "event",
        "object_id",
        "details",
        "timestamp_ns",
        "monotonic_ns",
        "sequence",
        "causal_parent",
        "event_hash",
    })
    _SHA256_LENGTH = 64

    def __init__(self, path: str | Path):
        self._journal = AppendJournal(path)
        self._sequence = 0
        self._last_hash = ""
        self._lock = threading.RLock()
        self.reload()

    @classmethod
    def _require_sha256(cls, value: object, field: str) -> str:
        if (
            not isinstance(value, str)
            or len(value) != cls._SHA256_LENGTH
            or any(char not in "0123456789abcdef" for char in value)
        ):
            raise ValueError(f"event {field} is invalid")
        return value

    @staticmethod
    def _require_nonnegative_int(value: object, field: str) -> int:
        if type(value) is not int or value < 0:
            raise ValueError(f"event {field} is invalid")
        return value

    @classmethod
    def _validate_payload_schema(cls, payload: object) -> dict[str, object]:
        if not isinstance(payload, dict) or set(payload) != cls._EVENT_FIELDS:
            raise ValueError("event schema verification failed")

        event = payload["event"]
        if not isinstance(event, str) or not event:
            raise ValueError("event event is invalid")

        object_id = payload["object_id"]
        if object_id is not None and (not isinstance(object_id, str) or not object_id):
            raise ValueError("event object_id is invalid")

        details = payload["details"]
        if not isinstance(details, dict):
            raise ValueError("event details are invalid")

        cls._require_nonnegative_int(payload["timestamp_ns"], "timestamp_ns")
        cls._require_nonnegative_int(payload["monotonic_ns"], "monotonic_ns")
        sequence = payload["sequence"]
        if type(sequence) is not int or sequence < 1:
            raise ValueError("event sequence is invalid")

        causal_parent = payload["causal_parent"]
        if causal_parent is not None:
            cls._require_sha256(causal_parent, "causal_parent")

        cls._require_sha256(payload["event_hash"], "event_hash")
        return payload

    def reload(self) -> None:
        """Refresh sequence/hash state from the journal after external coordination."""
        with self._lock:
            self._sequence = 0
            self._last_hash = ""
            for event in self.replay():
                self._sequence = event["sequence"]
                self._last_hash = event["event_hash"]

    def emit(self, event: str, *, object_id: str | None = None,
             details: dict[str, object] | None = None,
             causal_parent: str | None = None) -> dict[str, object]:
        with self._lock:
            sequence = self._sequence + 1
            payload = {
                "event": event,
                "object_id": object_id,
                "details": details or {},
                "timestamp_ns": time.time_ns(),
                "monotonic_ns": time.monotonic_ns(),
                "sequence": sequence,
                "causal_parent": causal_parent or self._last_hash or None,
            }
            payload["event_hash"] = hashlib.sha256(_canonical(payload)).hexdigest()
            record = self._journal.append("event", payload)
            self._sequence = sequence
            self._last_hash = payload["event_hash"]
            return record

    def replay(self) -> Iterator[dict[str, object]]:
        previous = ""
        expected_sequence = 1
        for record in self._journal.replay():
            if record.get("version") != FORMAT_VERSION or record.get("operation") != "event":
                continue
            payload = self._validate_payload_schema(record["payload"])
            event_hash = payload["event_hash"]
            body = dict(payload)
            body.pop("event_hash", None)
            if hashlib.sha256(_canonical(body)).hexdigest() != event_hash:
                raise ValueError("event hash verification failed")
            sequence = payload["sequence"]
            if sequence != expected_sequence:
                raise ValueError("event sequence verification failed")
            causal_parent = payload["causal_parent"]
            if causal_parent not in (None, previous):
                raise ValueError("event causal chain verification failed")
            previous = event_hash
            expected_sequence += 1
            yield payload
