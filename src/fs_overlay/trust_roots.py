"""Durable fail-closed trust-root registry for authenticated identity admission.

The registry stores public trust-anchor fingerprints only. It does not perform
cryptographic verification or store private key material. Verification remains
an injected ``PrincipalVerifier`` responsibility.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re

from .durable_coordination import FileAdmissionCoordinator
from .identity_verification import TrustRootStore

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True, slots=True)
class TrustRootRecord:
    sequence: int
    issuer_id: str
    fingerprint: str
    revoked: bool
    previous_digest: str
    event_digest: str

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            {
                "sequence": self.sequence,
                "issuer_id": self.issuer_id,
                "fingerprint": self.fingerprint,
                "revoked": self.revoked,
                "previous_digest": self.previous_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def create(
        cls,
        *,
        sequence: int,
        issuer_id: str,
        fingerprint: str,
        revoked: bool,
        previous_digest: str,
    ) -> "TrustRootRecord":
        if sequence < 1 or not issuer_id or not _SHA256_RE.fullmatch(fingerprint):
            raise ValueError("invalid trust-root record")
        if not _SHA256_RE.fullmatch(previous_digest):
            raise ValueError("invalid trust-root previous digest")
        record = cls(sequence, issuer_id, fingerprint.lower(), revoked, previous_digest.lower(), "")
        return cls(
            record.sequence,
            record.issuer_id,
            record.fingerprint,
            record.revoked,
            record.previous_digest,
            hashlib.sha256(record.canonical_bytes()).hexdigest(),
        )

    def to_line(self) -> str:
        return json.dumps(
            {
                "sequence": self.sequence,
                "issuer_id": self.issuer_id,
                "fingerprint": self.fingerprint,
                "revoked": self.revoked,
                "previous_digest": self.previous_digest,
                "event_digest": self.event_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_line(cls, line: str) -> "TrustRootRecord":
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                raise ValueError
            record = cls(
                int(data["sequence"]),
                str(data["issuer_id"]),
                str(data["fingerprint"]),
                bool(data["revoked"]),
                str(data["previous_digest"]),
                str(data["event_digest"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("malformed trust-root record") from exc
        if not record.issuer_id or not _SHA256_RE.fullmatch(record.fingerprint):
            raise ValueError("malformed trust-root fingerprint")
        if not _SHA256_RE.fullmatch(record.previous_digest):
            raise ValueError("malformed trust-root previous digest")
        if record.event_digest != hashlib.sha256(record.canonical_bytes()).hexdigest():
            raise ValueError("trust-root event digest mismatch")
        return record


class DurableTrustRootStore(TrustRootStore):
    """Append-only trust-root store with restart-safe fail-closed reads."""

    def __init__(self, path: str | Path, *, coordination_timeout: float = 5.0):
        if coordination_timeout < 0:
            raise ValueError("coordination_timeout must be non-negative")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._coordinator = FileAdmissionCoordinator(
            self.path.parent / ".trust-root-locks", timeout=coordination_timeout
        )
        with self._coordinator.acquire(str(self.path.resolve())):
            self._records = self._replay()

    def _replay(self) -> list[TrustRootRecord]:
        if not self.path.exists():
            return []
        records: list[TrustRootRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    raise ValueError(f"blank trust-root record at line {line_number}")
                record = TrustRootRecord.from_line(line)
                if record.sequence != len(records) + 1:
                    raise ValueError("trust-root sequence discontinuity")
                previous = records[-1].event_digest if records else "0" * 64
                if record.previous_digest != previous:
                    raise ValueError("trust-root hash-chain break")
                records.append(record)
        return records

    @staticmethod
    def _active(records: list[TrustRootRecord], issuer_id: str) -> str | None:
        fingerprint: str | None = None
        for record in records:
            if record.issuer_id == issuer_id:
                fingerprint = None if record.revoked else record.fingerprint
        return fingerprint

    def _append(self, *, issuer_id: str, fingerprint: str, revoked: bool) -> TrustRootRecord:
        if not issuer_id or not _SHA256_RE.fullmatch(fingerprint):
            raise ValueError("issuer_id and a SHA-256 fingerprint are required")
        with self._coordinator.acquire(str(self.path.resolve())):
            self._records = self._replay()
            previous = self._records[-1].event_digest if self._records else "0" * 64
            record = TrustRootRecord.create(
                sequence=len(self._records) + 1,
                issuer_id=issuer_id,
                fingerprint=fingerprint,
                revoked=revoked,
                previous_digest=previous,
            )
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(record.to_line() + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._records.append(record)
            return record

    def trust(self, issuer_id: str, fingerprint: str) -> TrustRootRecord:
        """Add or rotate an issuer trust root."""
        return self._append(issuer_id=issuer_id, fingerprint=fingerprint, revoked=False)

    def revoke(self, issuer_id: str) -> TrustRootRecord:
        """Revoke the currently trusted issuer; later trust() may rotate it."""
        with self._coordinator.acquire(str(self.path.resolve())):
            self._records = self._replay()
            current = self._active(self._records, issuer_id)
            if current is None:
                raise ValueError("issuer is not trusted")
            return self._append(issuer_id=issuer_id, fingerprint=current, revoked=True)

    def issuer_fingerprint(self, issuer_id: str) -> str | None:
        if not issuer_id:
            raise ValueError("issuer_id is required")
        with self._coordinator.acquire(str(self.path.resolve())):
            self._records = self._replay()
            return self._active(self._records, issuer_id)

    def records(self) -> tuple[TrustRootRecord, ...]:
        with self._coordinator.acquire(str(self.path.resolve())):
            self._records = self._replay()
            return tuple(self._records)
