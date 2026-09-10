"""Structured append-only event records for storage operations."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterator

from .storage_engine import AppendJournal, FORMAT_VERSION


class EventLog:
    def __init__(self, path: str | Path):
        self._journal = AppendJournal(path)

    def emit(self, event: str, *, object_id: str | None = None, details: dict[str, object] | None = None) -> dict[str, object]:
        payload = {"event": event, "object_id": object_id, "details": details or {}, "timestamp_ns": time.time_ns()}
        return self._journal.append("event", payload)

    def replay(self) -> Iterator[dict[str, object]]:
        for record in self._journal.replay():
            if record.get("version") == FORMAT_VERSION and record.get("operation") == "event":
                yield record["payload"]
