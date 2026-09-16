"""Durable fail-closed node and key admission registries.

Only public identity metadata is persisted. Private key material and cryptographic
verification remain deployment responsibilities supplied through injected adapters.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re

from .durable_coordination import FileAdmissionCoordinator
from .production_adapters import KeyAdmission, NodeAdmission

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ZERO = "0" * 64
_NODE_ADMISSION_FIELDS = frozenset(
    {"sequence", "node_id", "fingerprint", "revoked", "previous_digest", "event_digest"}
)
_KEY_ADMISSION_FIELDS = frozenset(
    {"sequence", "node_id", "key_id", "fingerprint", "status", "previous_digest", "event_digest"}
)


def _valid_digest(value: str) -> bool:
    return bool(_SHA256_RE.fullmatch(value))


def _canonical(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _reject_duplicate_object_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject ambiguous JSON objects before durable admission validation."""
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value


@dataclass(frozen=True, slots=True)
class NodeAdmissionRecord:
    sequence: int
    node_id: str
    fingerprint: str
    revoked: bool
    previous_digest: str
    event_digest: str

    def canonical_bytes(self) -> bytes:
        return _canonical({"sequence": self.sequence, "node_id": self.node_id,
                           "fingerprint": self.fingerprint, "revoked": self.revoked,
                           "previous_digest": self.previous_digest})

    @classmethod
    def create(cls, *, sequence: int, node_id: str, fingerprint: str,
               revoked: bool, previous_digest: str) -> "NodeAdmissionRecord":
        if sequence < 1 or not node_id or not _valid_digest(fingerprint.lower()):
            raise ValueError("invalid node admission record")
        if not _valid_digest(previous_digest.lower()) or not isinstance(revoked, bool):
            raise ValueError("invalid node admission record")
        record = cls(sequence, node_id, fingerprint.lower(), revoked, previous_digest.lower(), "")
        return cls(record.sequence, record.node_id, record.fingerprint, record.revoked,
                   record.previous_digest, hashlib.sha256(record.canonical_bytes()).hexdigest())

    def to_line(self) -> str:
        return json.dumps({"sequence": self.sequence, "node_id": self.node_id,
                           "fingerprint": self.fingerprint, "revoked": self.revoked,
                           "previous_digest": self.previous_digest, "event_digest": self.event_digest},
                          sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_line(cls, line: str) -> "NodeAdmissionRecord":
        try:
            data = json.loads(line, object_pairs_hook=_reject_duplicate_object_keys)
            if not isinstance(data, dict) or set(data) != _NODE_ADMISSION_FIELDS:
                raise ValueError
            if not isinstance(data["sequence"], int) or isinstance(data["sequence"], bool):
                raise ValueError
            if not isinstance(data["node_id"], str):
                raise ValueError
            if not isinstance(data["fingerprint"], str):
                raise ValueError
            if not isinstance(data["revoked"], bool):
                raise ValueError
            if not isinstance(data["previous_digest"], str):
                raise ValueError
            if not isinstance(data["event_digest"], str):
                raise ValueError
            record = cls(data["sequence"], data["node_id"], data["fingerprint"], data["revoked"],
                         data["previous_digest"], data["event_digest"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("malformed node admission record") from exc
        if (record.sequence < 1 or not record.node_id or not _valid_digest(record.fingerprint)
                or not _valid_digest(record.previous_digest) or not _valid_digest(record.event_digest)
                or record.event_digest != hashlib.sha256(record.canonical_bytes()).hexdigest()):
            raise ValueError("malformed node admission record")
        return record


class DurableNodeAdmission(NodeAdmission):
    """Append-only node admission with restart-safe cross-process serialization."""

    def __init__(self, path: str | Path, *, coordination_timeout: float = 5.0):
        if coordination_timeout < 0:
            raise ValueError("coordination_timeout must be non-negative")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = FileAdmissionCoordinator(self.path.parent / ".node-admission-locks", timeout=coordination_timeout)
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay()

    def _replay(self) -> list[NodeAdmissionRecord]:
        if not self.path.exists():
            return []
        out = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    raise ValueError("blank node admission record")
                r = NodeAdmissionRecord.from_line(line)
                if r.sequence != len(out) + 1 or r.previous_digest != (out[-1].event_digest if out else _ZERO):
                    raise ValueError("node admission journal chain break")
                out.append(r)
        return out

    def _current_record(self, node_id: str) -> NodeAdmissionRecord | None:
        current = None
        for record in self._records:
            if record.node_id == node_id:
                current = record
        return current

    def _current(self, node_id: str) -> str | None:
        record = self._current_record(node_id)
        return None if record is None or record.revoked else record.fingerprint

    def _append(self, node_id: str, fingerprint: str, revoked: bool) -> None:
        r = NodeAdmissionRecord.create(sequence=len(self._records) + 1, node_id=node_id,
                                       fingerprint=fingerprint, revoked=revoked,
                                       previous_digest=self._records[-1].event_digest if self._records else _ZERO)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(r.to_line() + "\n"); f.flush(); os.fsync(f.fileno())
        self._records.append(r)

    def admit(self, node_id: str, public_key_fingerprint: str) -> bool:
        if not node_id or not _valid_digest(public_key_fingerprint.lower()):
            return False
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay()
            current_record = self._current_record(node_id)
            if current_record is not None:
                if current_record.revoked:
                    return False
                if current_record.fingerprint != public_key_fingerprint.lower():
                    return False
            self._append(node_id, public_key_fingerprint, False)
            return True

    def revoke(self, node_id: str, reason: str = "") -> None:
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay(); current = self._current(node_id)
            if current is None:
                raise ValueError("node is not admitted")
            self._append(node_id, current, True)

    def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool:
        if not node_id or not _valid_digest(public_key_fingerprint.lower()):
            return False
        try:
            with self._lock.acquire(str(self.path.resolve())):
                self._records = self._replay()
                return self._current(node_id) == public_key_fingerprint.lower()
        except (OSError, ValueError):
            return False

    def records(self) -> tuple[NodeAdmissionRecord, ...]:
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay(); return tuple(self._records)


@dataclass(frozen=True, slots=True)
class KeyAdmissionRecord:
    sequence: int
    node_id: str
    key_id: str
    fingerprint: str
    status: str
    previous_digest: str
    event_digest: str

    def canonical_bytes(self) -> bytes:
        return _canonical({"sequence": self.sequence, "node_id": self.node_id, "key_id": self.key_id,
                           "fingerprint": self.fingerprint, "status": self.status,
                           "previous_digest": self.previous_digest})

    @classmethod
    def create(cls, *, sequence: int, node_id: str, key_id: str, fingerprint: str,
               status: str, previous_digest: str) -> "KeyAdmissionRecord":
        if (sequence < 1 or not node_id or not key_id or not _valid_digest(fingerprint.lower())
                or status not in {"ACTIVE", "RETIRED", "REVOKED"} or not _valid_digest(previous_digest.lower())):
            raise ValueError("invalid key admission record")
        r = cls(sequence, node_id, key_id, fingerprint.lower(), status, previous_digest.lower(), "")
        return cls(r.sequence, r.node_id, r.key_id, r.fingerprint, r.status, r.previous_digest,
                   hashlib.sha256(r.canonical_bytes()).hexdigest())

    def to_line(self) -> str:
        return json.dumps({"sequence": self.sequence, "node_id": self.node_id, "key_id": self.key_id,
                           "fingerprint": self.fingerprint, "status": self.status,
                           "previous_digest": self.previous_digest, "event_digest": self.event_digest},
                          sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_line(cls, line: str) -> "KeyAdmissionRecord":
        try:
            data = json.loads(line, object_pairs_hook=_reject_duplicate_object_keys)
            if not isinstance(data, dict) or set(data) != _KEY_ADMISSION_FIELDS:
                raise ValueError
            if not isinstance(data["sequence"], int) or isinstance(data["sequence"], bool):
                raise ValueError
            if not isinstance(data["node_id"], str):
                raise ValueError
            if not isinstance(data["key_id"], str):
                raise ValueError
            if not isinstance(data["fingerprint"], str):
                raise ValueError
            if not isinstance(data["status"], str):
                raise ValueError
            if not isinstance(data["previous_digest"], str):
                raise ValueError
            if not isinstance(data["event_digest"], str):
                raise ValueError
            record = cls(data["sequence"], data["node_id"], data["key_id"], data["fingerprint"],
                         data["status"], data["previous_digest"], data["event_digest"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("malformed key admission record") from exc
        if (record.sequence < 1 or not record.node_id or not record.key_id or not _valid_digest(record.fingerprint)
                or record.status not in {"ACTIVE", "RETIRED", "REVOKED"} or not _valid_digest(record.previous_digest)
                or not _valid_digest(record.event_digest) or record.event_digest != hashlib.sha256(record.canonical_bytes()).hexdigest()):
            raise ValueError("malformed key admission record")
        return record


class DurableKeyAdmission(KeyAdmission):
    """Append-only node/key binding with explicit ACTIVE/RETIRED/REVOKED gates."""

    def __init__(self, path: str | Path, *, coordination_timeout: float = 5.0):
        if coordination_timeout < 0:
            raise ValueError("coordination_timeout must be non-negative")
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = FileAdmissionCoordinator(self.path.parent / ".key-admission-locks", timeout=coordination_timeout)
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay()

    def _replay(self) -> list[KeyAdmissionRecord]:
        if not self.path.exists(): return []
        out = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): raise ValueError("blank key admission record")
                r = KeyAdmissionRecord.from_line(line)
                if r.sequence != len(out) + 1 or r.previous_digest != (out[-1].event_digest if out else _ZERO):
                    raise ValueError("key admission journal chain break")
                out.append(r)
        return out

    def _current(self, node_id: str, key_id: str) -> KeyAdmissionRecord | None:
        current = None
        for r in self._records:
            if r.node_id == node_id and r.key_id == key_id: current = r
        return current

    def _append(self, node_id: str, key_id: str, fingerprint: str, status: str) -> None:
        r = KeyAdmissionRecord.create(sequence=len(self._records) + 1, node_id=node_id, key_id=key_id,
                                      fingerprint=fingerprint, status=status,
                                      previous_digest=self._records[-1].event_digest if self._records else _ZERO)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(r.to_line() + "\n"); f.flush(); os.fsync(f.fileno())
        self._records.append(r)

    def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool:
        if not node_id or not key_id or not _valid_digest(fingerprint.lower()): return False
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay(); current = self._current(node_id, key_id)
            if current is not None and (
                current.fingerprint != fingerprint.lower()
                or current.status in {"RETIRED", "REVOKED"}
            ):
                return False
            self._append(node_id, key_id, fingerprint, "ACTIVE"); return True

    def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None:
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay(); current = self._current(node_id, key_id)
            if current is None or current.status == "REVOKED": raise ValueError("key is not admitted")
            self._append(node_id, key_id, current.fingerprint, "REVOKED")

    def retire_key(self, node_id: str, key_id: str) -> None:
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay(); current = self._current(node_id, key_id)
            if current is None or current.status == "REVOKED": raise ValueError("key is not active")
            if current.status == "RETIRED": return
            self._append(node_id, key_id, current.fingerprint, "RETIRED")

    def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool:
        if not node_id or not key_id or not _valid_digest(fingerprint.lower()): return False
        try:
            with self._lock.acquire(str(self.path.resolve())):
                self._records = self._replay(); r = self._current(node_id, key_id)
                return r is not None and r.fingerprint == fingerprint.lower() and r.status != "REVOKED"
        except (OSError, ValueError): return False

    def can_sign(self, node_id: str, key_id: str) -> bool:
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay(); r = self._current(node_id, key_id)
            return r is not None and r.status == "ACTIVE"

    def can_verify(self, node_id: str, key_id: str) -> bool:
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay(); r = self._current(node_id, key_id)
            return r is not None and r.status in {"ACTIVE", "RETIRED"}

    def records(self) -> tuple[KeyAdmissionRecord, ...]:
        with self._lock.acquire(str(self.path.resolve())):
            self._records = self._replay(); return tuple(self._records)
