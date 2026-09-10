"""Key lifecycle state machine; cryptographic operations remain injected."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class KeyRecord:
    key_id: str
    fingerprint: str
    status: str = "ACTIVE"


class KeyLifecycle:
    """Explicit key state with deterministic rotation and revocation rules."""

    def __init__(self, records: Iterable[KeyRecord] = ()):
        self.records = {record.key_id: record for record in records}

    def active(self) -> tuple[KeyRecord, ...]:
        return tuple(sorted((r for r in self.records.values() if r.status == "ACTIVE"), key=lambda r: r.key_id))

    def rotate(self, record: KeyRecord) -> None:
        if not record.key_id or not record.fingerprint:
            raise ValueError("key_id and fingerprint are required")
        for key_id, current in tuple(self.records.items()):
            if current.status == "ACTIVE":
                self.records[key_id] = KeyRecord(current.key_id, current.fingerprint, "RETIRED")
        self.records[record.key_id] = KeyRecord(record.key_id, record.fingerprint, "ACTIVE")

    def revoke(self, key_id: str) -> None:
        current = self.records.get(key_id)
        if current is None:
            return
        self.records[key_id] = KeyRecord(current.key_id, current.fingerprint, "REVOKED")

    def usable(self, key_id: str) -> bool:
        record = self.records.get(key_id)
        return record is not None and record.status == "ACTIVE"
