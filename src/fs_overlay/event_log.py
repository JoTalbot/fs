"""Structured append-only event records for storage and control operations."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Iterator

from .storage_engine import AppendJournal, FORMAT_VERSION, _canonical


class EventLog:
    """Event facade with explicit sequence, monotonic timestamp and causal parent."""

    def __init__(self, path: str | Path):
        self._journal = AppendJournal(path)
        self._sequence = 0
        self._last_hash = ""
        for event in self.replay():
            self._sequence = max(self._sequence, int(event.get("sequence", 0)))
            self._last_hash = str(event.get("event_hash", self._last_hash))

    def emit(self, event: str, *, object_id: str | None = None,
             details: dict[str, object] | None = None,
             causal_parent: str | None = None) -> dict[str, object]:
        self._sequence += 1
        payload = {
            "event": event,
            "object_id": object_id,
            "details": details or {},
            "timestamp_ns": time.time_ns(),
            "monotonic_ns": time.monotonic_ns(),
            "sequence": self._sequence,
            "causal_parent": causal_parent or self._last_hash or None,
        }
        payload["event_hash"] = hashlib.sha256(_canonical(payload)).hexdigest()
        record = self._journal.append("event", payload)
        self._last_hash = str(payload["event_hash"])
        return record

    def replay(self) -> Iterator[dict[str, object]]:
        previous = ""
        expected_sequence = 1
        for record in self._journal.replay():
            if record.get("version") != FORMAT_VERSION or record.get("operation") != "event":
                continue
            payload = record["payload"]
            if not isinstance(payload, dict):
                continue
            event_hash = payload.get("event_hash")
            if event_hash:
                body = dict(payload)
                body.pop("event_hash", None)
                if hashlib.sha256(_canonical(body)).hexdigest() != event_hash:
                    raise ValueError("event hash verification failed")
                sequence = int(payload.get("sequence", 0))
                if sequence != expected_sequence:
                    raise ValueError("event sequence verification failed")
                causal_parent = payload.get("causal_parent")
                if causal_parent not in (None, previous):
                    raise ValueError("event causal chain verification failed")
                previous = str(event_hash)
                expected_sequence += 1
            yield payload
