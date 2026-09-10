"""Key lifecycle state machine; cryptographic operations remain injected."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


_ALLOWED_STATUSES = frozenset({"ACTIVE", "RETIRED", "REVOKED"})


@dataclass(frozen=True)
class KeyRecord:
    key_id: str
    fingerprint: str
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        if not self.key_id or not self.fingerprint:
            raise ValueError("key_id and fingerprint are required")
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError(f"unsupported key status: {self.status}")


class KeyLifecycle:
    """Explicit key state with deterministic rotation and revocation rules."""

    def __init__(self, records: Iterable[KeyRecord] = ()):
        materialized = tuple(records)
        ids = [record.key_id for record in materialized]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate key_id")
        active = [record for record in materialized if record.status == "ACTIVE"]
        if len(active) > 1:
            raise ValueError("at most one active key is permitted")
        self.records = {record.key_id: record for record in materialized}

    def active(self) -> tuple[KeyRecord, ...]:
        return tuple(sorted((r for r in self.records.values() if r.status == "ACTIVE"), key=lambda r: r.key_id))

    def rotate(self, record: KeyRecord) -> None:
        if record.status != "ACTIVE":
            raise ValueError("rotation requires an ACTIVE key")
        current = self.records.get(record.key_id)
        if current is not None and current.fingerprint != record.fingerprint:
            raise ValueError("key_id fingerprint cannot change silently")
        for key_id, existing in tuple(self.records.items()):
            if existing.status == "ACTIVE" and key_id != record.key_id:
                self.records[key_id] = KeyRecord(existing.key_id, existing.fingerprint, "RETIRED")
        self.records[record.key_id] = record

    def revoke(self, key_id: str) -> None:
        current = self.records.get(key_id)
        if current is None:
            return
        self.records[key_id] = KeyRecord(current.key_id, current.fingerprint, "REVOKED")

    def usable(self, key_id: str) -> bool:
        """Backward-compatible alias for keys currently allowed to sign."""
        return self.usable_for_signing(key_id)

    def usable_for_signing(self, key_id: str) -> bool:
        record = self.records.get(key_id)
        return record is not None and record.status == "ACTIVE"

    def usable_for_verification(self, key_id: str) -> bool:
        """Allow active and retired keys for verification; never revoked keys."""
        record = self.records.get(key_id)
        return record is not None and record.status in {"ACTIVE", "RETIRED"}

    def fingerprint_for(self, key_id: str) -> str | None:
        record = self.records.get(key_id)
        return None if record is None else record.fingerprint
