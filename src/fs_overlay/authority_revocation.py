"""Durable fail-closed revocation boundary for transfer authority.

Revocation is intentionally separate from recovery audit. A recovery audit event
records a decision; this registry is the source used by a future executor to
determine whether an authority has been revoked. It stores no secrets and
provides no authentication or filesystem mutation.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
import os
from pathlib import Path

from .durable_coordination import FileAdmissionCoordinator


def _reject_duplicate_object_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject ambiguous JSON objects before schema or integrity validation."""
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value


@dataclass(frozen=True, slots=True)
class RevocationRecord:
    sequence: int
    authority_id: str
    reason: str
    previous_digest: str
    event_digest: str

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            {"sequence": self.sequence, "authority_id": self.authority_id,
             "reason": self.reason, "previous_digest": self.previous_digest},
            sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def create(cls, *, sequence: int, authority_id: str, reason: str,
               previous_digest: str) -> "RevocationRecord":
        if sequence < 1 or not authority_id or not reason:
            raise ValueError("invalid revocation record")
        canonical = json.dumps(
            {"sequence": sequence, "authority_id": authority_id,
             "reason": reason, "previous_digest": previous_digest},
            sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        return cls(sequence, authority_id, reason, previous_digest,
                   hashlib.sha256(canonical).hexdigest())

    def to_line(self) -> str:
        return json.dumps({
            "sequence": self.sequence, "authority_id": self.authority_id,
            "reason": self.reason, "previous_digest": self.previous_digest,
            "event_digest": self.event_digest,
        }, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_line(cls, line: str) -> "RevocationRecord":
        try:
            data = json.loads(line, object_pairs_hook=_reject_duplicate_object_keys)
            if not isinstance(data, dict):
                raise ValueError
            if set(data) != {
                "sequence", "authority_id", "reason", "previous_digest", "event_digest"
            }:
                raise ValueError
            if (
                type(data["sequence"]) is not int
                or type(data["authority_id"]) is not str
                or type(data["reason"]) is not str
                or type(data["previous_digest"]) is not str
                or type(data["event_digest"]) is not str
            ):
                raise ValueError
            record = cls(
                data["sequence"], data["authority_id"], data["reason"],
                data["previous_digest"], data["event_digest"],
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("malformed revocation record") from exc
        if record.event_digest != hashlib.sha256(record.canonical_bytes()).hexdigest():
            raise ValueError("revocation event digest mismatch")
        return record


class AuthorityRevocationRegistry:
    """Append-only revocation registry with fail-closed restart/replay.

    All replay and mutation decisions are serialized through the same
    cross-process OS lock. The registry therefore does not rely on a stale
    in-memory view when another process revokes an authority concurrently.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        coordination_timeout: float = 5.0,
    ):
        if coordination_timeout < 0:
            raise ValueError("coordination_timeout must be non-negative")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._coordinator = FileAdmissionCoordinator(
            self.path.parent / ".revocation-locks",
            timeout=coordination_timeout,
        )
        with self._coordinator.acquire(str(self.path.resolve())):
            self._records = self._replay()

    def _replay(self) -> list[RevocationRecord]:
        if not self.path.exists():
            return []
        records: list[RevocationRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    raise ValueError(f"blank revocation record at line {line_number}")
                record = RevocationRecord.from_line(line)
                if record.sequence != len(records) + 1:
                    raise ValueError("revocation sequence discontinuity")
                previous = records[-1].event_digest if records else "0" * 64
                if record.previous_digest != previous:
                    raise ValueError("revocation hash-chain break")
                if any(item.authority_id == record.authority_id for item in records):
                    raise ValueError("duplicate authority revocation")
                records.append(record)
        return records

    @staticmethod
    def _is_revoked(records: list[RevocationRecord], authority_id: str) -> bool:
        return any(item.authority_id == authority_id for item in records)

    def revoke(self, authority_id: str, *, reason: str) -> RevocationRecord:
        if not authority_id or not reason:
            raise ValueError("authority_id and reason are required")
        with self._coordinator.acquire(str(self.path.resolve())):
            # Refresh while holding the lock so independent registry instances
            # cannot make decisions from an obsolete in-memory snapshot.
            self._records = self._replay()
            if self._is_revoked(self._records, authority_id):
                raise ValueError("authority is already revoked")
            previous = self._records[-1].event_digest if self._records else "0" * 64
            record = RevocationRecord.create(
                sequence=len(self._records) + 1, authority_id=authority_id,
                reason=reason, previous_digest=previous,
            )
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(record.to_line() + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._records.append(record)
            return record

    def is_revoked(self, authority_id: str) -> bool:
        if not authority_id:
            raise ValueError("authority_id is required")
        with self._coordinator.acquire(str(self.path.resolve())):
            self._records = self._replay()
            return self._is_revoked(self._records, authority_id)

    def records(self) -> tuple[RevocationRecord, ...]:
        with self._coordinator.acquire(str(self.path.resolve())):
            self._records = self._replay()
            return tuple(self._records)
