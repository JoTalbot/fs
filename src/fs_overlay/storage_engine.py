"""Dependency-free local FS storage engine foundation."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator, Protocol

FORMAT_VERSION = 1
DEFAULT_CHUNK_SIZE = 1024 * 1024


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _fsync_directory(directory: str | Path) -> None:
    """Persist directory-entry changes where the platform exposes that contract."""
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    fd = os.open(Path(directory), flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _reject_duplicate_object_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject ambiguous JSON objects before schema or integrity validation."""
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value


@dataclass(frozen=True)
class Manifest:
    object_id: str
    size: int
    chunks: tuple[str, ...]
    chunk_size: int
    format_version: int = FORMAT_VERSION
    metadata: dict[str, str] | None = None

    def unsigned(self) -> dict[str, object]:
        return {"size": self.size, "chunks": self.chunks, "chunk_size": self.chunk_size,
                "format_version": self.format_version, "metadata": self.metadata}

    def identity(self) -> str:
        return hashlib.sha256(_canonical(self.unsigned())).hexdigest()

    def to_bytes(self) -> bytes:
        return _canonical(asdict(self))

    @staticmethod
    def _require_object_id(value: object, field: str = "object_id") -> str:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)
        ):
            raise ValueError(f"manifest {field} is invalid")
        return value

    @staticmethod
    def _require_non_negative_int(value: object, field: str) -> int:
        if type(value) is not int or value < 0:
            raise ValueError(f"manifest {field} is invalid")
        return value

    @classmethod
    def from_bytes(cls, data: bytes) -> "Manifest":
        try:
            raw = json.loads(data, object_pairs_hook=_reject_duplicate_object_keys)
        except (TypeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("manifest JSON is invalid") from exc
        if not isinstance(raw, dict):
            raise ValueError("manifest schema is invalid")
        expected_fields = {"object_id", "size", "chunks", "chunk_size", "format_version", "metadata"}
        if set(raw) != expected_fields:
            raise ValueError("manifest schema is invalid")
        if type(raw["format_version"]) is not int or raw["format_version"] != FORMAT_VERSION:
            raise ValueError("unsupported manifest format version")
        object_id = cls._require_object_id(raw["object_id"])
        size = cls._require_non_negative_int(raw["size"], "size")
        chunks = raw["chunks"]
        if not isinstance(chunks, list):
            raise ValueError("manifest chunks are invalid")
        validated_chunks = tuple(cls._require_object_id(chunk, "chunk id") for chunk in chunks)
        chunk_size = raw["chunk_size"]
        if type(chunk_size) is not int or chunk_size <= 0:
            raise ValueError("manifest chunk_size is invalid")
        metadata = raw["metadata"]
        if metadata is not None:
            if not isinstance(metadata, dict) or any(
                not isinstance(key, str) or not isinstance(value, str)
                for key, value in metadata.items()
            ):
                raise ValueError("manifest metadata is invalid")
            metadata = dict(metadata)
        result = cls(object_id, size, validated_chunks, chunk_size, raw["format_version"], metadata)
        if result.identity() != result.object_id:
            raise ValueError("manifest identity verification failed")
        return result


class DeterministicChunker:
    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size

    def split(self, data: bytes) -> Iterator[bytes]:
        for offset in range(0, len(data), self.chunk_size):
            yield data[offset:offset + self.chunk_size]

    def split_stream(self, stream: BinaryIO) -> Iterator[bytes]:
        while chunk := stream.read(self.chunk_size):
            yield chunk


class AuthenticatedEncryption(Protocol):
    """Provider boundary. Production deployments must supply audited AEAD."""
    name: str

    def encrypt(self, plaintext: bytes, *, associated_data: bytes = b"") -> bytes: ...
    def decrypt(self, ciphertext: bytes, *, associated_data: bytes = b"") -> bytes: ...


class HMACIntegrityEnvelope:
    """Integrity-only development envelope; it provides no confidentiality."""
    name = "hmac-integrity-envelope"

    def __init__(self, key: bytes):
        if len(key) < 16:
            raise ValueError("integrity key must be at least 16 bytes")
        self._key = key

    def encrypt(self, plaintext: bytes, *, associated_data: bytes = b"") -> bytes:
        return hmac.new(self._key, associated_data + plaintext, hashlib.sha256).digest() + plaintext

    def decrypt(self, ciphertext: bytes, *, associated_data: bytes = b"") -> bytes:
        if len(ciphertext) < 32:
            raise ValueError("invalid integrity envelope")
        tag, plaintext = ciphertext[:32], ciphertext[32:]
        expected = hmac.new(self._key, associated_data + plaintext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            raise ValueError("integrity verification failed")
        return plaintext


class ErasureCoder(Protocol):
    name: str

    def encode(self, shards: list[bytes], *, parity_shards: int) -> list[bytes]: ...
    def recover(self, shards: list[bytes | None], *, data_shards: int, parity_shards: int) -> list[bytes]: ...


@dataclass(frozen=True)
class ObjectRecord:
    object_id: str
    size: int
    manifest_path: str


class ContentAddressedStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.objects = self.root / "objects"
        self.manifests = self.root / "manifests"
        self.objects.mkdir(parents=True, exist_ok=True)
        self.manifests.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def object_id(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _path(self, object_id: str) -> Path:
        if len(object_id) != 64 or any(c not in "0123456789abcdef" for c in object_id):
            raise ValueError("invalid object id")
        directory = self.objects / object_id[:2]
        directory.mkdir(exist_ok=True)
        return directory / object_id

    def put(self, data: bytes) -> str:
        oid = self.object_id(data)
        target = self._path(oid)
        if target.exists():
            if self.object_id(target.read_bytes()) != oid:
                raise IOError("object collision or corruption")
            return oid
        fd, temporary = tempfile.mkstemp(prefix=".tmp-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
            _fsync_directory(target.parent)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return oid

    def get(self, object_id: str) -> bytes:
        data = self._path(object_id).read_bytes()
        if self.object_id(data) != object_id:
            raise IOError("object integrity check failed")
        return data

    def put_manifest(self, manifest: Manifest) -> str:
        if manifest.identity() != manifest.object_id:
            raise ValueError("manifest identity does not match")
        target = self.manifests / manifest.object_id
        if not target.exists():
            fd, temporary = tempfile.mkstemp(prefix=".tmp-", dir=self.manifests)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(manifest.to_bytes())
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
                _fsync_directory(self.manifests)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        return manifest.object_id

    def get_manifest(self, object_id: str) -> Manifest:
        if not isinstance(object_id, str) or len(object_id) != 64 or any(c not in "0123456789abcdef" for c in object_id):
            raise ValueError("invalid object id")
        manifest = Manifest.from_bytes((self.manifests / object_id).read_bytes())
        if manifest.object_id != object_id:
            raise ValueError("manifest identity verification failed")
        return manifest


class JournalCorruption(ValueError):
    """A journal frame is complete enough to prove corruption, not truncation."""


class AppendJournal:
    """Length-prefixed JSON journal; only an incomplete EOF tail is ignored on replay."""
    _RECORD_FIELDS = frozenset({"version", "operation", "payload"})

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, operation: str, payload: dict[str, object]) -> dict[str, object]:
        record = {"version": FORMAT_VERSION, "operation": operation, "payload": payload}
        encoded = _canonical(record)
        with self.path.open("ab") as handle:
            handle.write(f"{len(encoded):016x}".encode() + encoded + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        return record

    def replay(self) -> Iterator[dict[str, object]]:
        if not self.path.exists():
            return
        with self.path.open("rb") as handle:
            while True:
                line = handle.readline()
                if not line:
                    return
                if len(line) < 17:
                    if handle.peek(1):
                        raise JournalCorruption("journal contains a malformed non-tail frame")
                    return
                try:
                    size = int(line[:16], 16)
                except ValueError as exc:
                    raise JournalCorruption("journal frame length is malformed") from exc
                body = line[16:-1]
                if len(body) != size:
                    if handle.peek(1):
                        raise JournalCorruption("journal frame is truncated before later records")
                    return
                try:
                    record = json.loads(body)
                except json.JSONDecodeError as exc:
                    raise JournalCorruption("journal contains malformed JSON") from exc
                if not isinstance(record, dict) or set(record) != self._RECORD_FIELDS:
                    raise JournalCorruption("journal record schema is invalid")
                if type(record["version"]) is not int or record["version"] != FORMAT_VERSION:
                    raise JournalCorruption("journal record version is invalid")
                if not isinstance(record["operation"], str) or not record["operation"]:
                    raise JournalCorruption("journal operation is invalid")
                if not isinstance(record["payload"], dict):
                    raise JournalCorruption("journal payload is invalid")
                yield record


class Inventory:
    _HEX_ID_LENGTH = 64
    _OPERATIONS = frozenset({"transaction_begin", "transaction_commit", "transaction_abort", "commit", "delete"})

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.records: dict[str, ObjectRecord] = {}
        self.load()

    @classmethod
    def _require_nonempty_string(cls, value: object, field: str) -> str:
        if not isinstance(value, str) or not value:
            raise JournalCorruption(f"journal {field} must be a non-empty string")
        return value

    @classmethod
    def _require_object_id(cls, value: object) -> str:
        if (
            not isinstance(value, str)
            or len(value) != cls._HEX_ID_LENGTH
            or any(char not in "0123456789abcdef" for char in value)
        ):
            raise JournalCorruption("journal object_id is invalid")
        return value

    @classmethod
    def _validate_payload(cls, operation: str, payload: dict[str, object]) -> None:
        if operation not in cls._OPERATIONS:
            raise JournalCorruption("journal operation is invalid")
        if operation in {"transaction_begin", "transaction_abort"}:
            if set(payload) != {"transaction_id"}:
                raise JournalCorruption("journal transaction payload schema is invalid")
            cls._require_nonempty_string(payload["transaction_id"], "transaction_id")
            return
        if operation == "transaction_commit":
            if set(payload) != {"transaction_id", "object_ids"}:
                raise JournalCorruption("journal transaction commit schema is invalid")
            cls._require_nonempty_string(payload["transaction_id"], "transaction_id")
            object_ids = payload["object_ids"]
            if not isinstance(object_ids, list):
                raise JournalCorruption("journal object_ids must be a list")
            for object_id in object_ids:
                cls._require_object_id(object_id)
            return
        if operation == "delete":
            if set(payload) != {"object_id"}:
                raise JournalCorruption("journal delete payload schema is invalid")
            cls._require_object_id(payload["object_id"])
            return
        allowed = {"object_id", "size", "manifest_path", "transaction_id"}
        if set(payload) - allowed or not {"object_id", "size", "manifest_path"}.issubset(payload):
            raise JournalCorruption("journal commit payload schema is invalid")
        cls._require_object_id(payload["object_id"])
        if type(payload["size"]) is not int or payload["size"] < 0:
            raise JournalCorruption("journal size must be a non-negative integer")
        manifest_path = cls._require_nonempty_string(payload["manifest_path"], "manifest_path")
        if manifest_path != payload["object_id"]:
            raise JournalCorruption("journal manifest_path does not match object_id")
        if "transaction_id" in payload:
            cls._require_nonempty_string(payload["transaction_id"], "transaction_id")

    def load(self) -> None:
        self.records.clear()
        pending: dict[str, list[dict[str, object]]] = {}
        for record in AppendJournal(self.path).replay():
            operation = record["operation"]
            payload = record["payload"]
            self._validate_payload(operation, payload)
            if operation == "transaction_begin":
                pending[payload["transaction_id"]] = []
                continue
            if operation == "transaction_commit":
                transaction_id = payload["transaction_id"]
                for staged in pending.pop(transaction_id, []):
                    self._apply_commit(staged)
                continue
            if operation == "transaction_abort":
                pending.pop(payload["transaction_id"], None)
                continue
            if operation == "commit":
                transaction_id = payload.get("transaction_id")
                if transaction_id is not None:
                    pending.setdefault(transaction_id, []).append(payload)
                else:
                    self._apply_commit(payload)
            elif operation == "delete":
                self.records.pop(payload["object_id"], None)

    def _apply_commit(self, payload: dict[str, object]) -> None:
        oid = payload["object_id"]
        self.records[oid] = ObjectRecord(oid, payload["size"], payload["manifest_path"])


class MerkleDAG:
    @staticmethod
    def leaf(value: bytes) -> str:
        return hashlib.sha256(b"leaf:" + value).hexdigest()

    @staticmethod
    def parent(children: Iterable[str]) -> str:
        ordered = tuple(children)
        if not ordered:
            raise ValueError("Merkle parent requires children")
        return hashlib.sha256(b"node:" + _canonical(ordered)).hexdigest()

    @classmethod
    def root(cls, leaves: Iterable[str]) -> str:
        level = list(leaves)
        if not level:
            return cls.leaf(b"")
        while len(level) > 1:
            next_level: list[str] = []
            for index in range(0, len(level), 2):
                pair = level[index:index + 2]
                next_level.append(cls.parent(pair))
            level = next_level
        return level[0]


class StorageTransaction:
    def __init__(self, engine: "LocalStorageEngine"):
        self.engine = engine
        self.transaction_id = uuid.uuid4().hex
        self._prepared: list[Manifest] = []
        self.engine.journal.append("transaction_begin", {"transaction_id": self.transaction_id})

    def prepare(self, data: bytes, *, metadata: dict[str, str] | None = None) -> Manifest:
        chunks = tuple(self.engine.store.put(chunk) for chunk in DeterministicChunker(self.engine.chunk_size).split(data))
        manifest = Manifest("", len(data), chunks, self.engine.chunk_size, FORMAT_VERSION, metadata)
        manifest = Manifest(manifest.identity(), manifest.size, manifest.chunks, manifest.chunk_size, manifest.format_version, manifest.metadata)
        self.engine.store.put_manifest(manifest)
        self._prepared.append(manifest)
        self.engine.journal.append("commit", {
            "object_id": manifest.object_id,
            "size": manifest.size,
            "manifest_path": manifest.object_id,
            "transaction_id": self.transaction_id,
        })
        return manifest

    def commit(self) -> tuple[Manifest, ...]:
        self.engine.journal.append("transaction_commit", {
            "transaction_id": self.transaction_id,
            "object_ids": [manifest.object_id for manifest in self._prepared],
        })
        return tuple(self._prepared)

    def rollback(self) -> None:
        self.engine.journal.append("transaction_abort", {"transaction_id": self.transaction_id})


class LocalStorageEngine:
    def __init__(self, root: str | Path, *, chunk_size: int = DEFAULT_CHUNK_SIZE):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.chunk_size = chunk_size
        self.store = ContentAddressedStore(self.root / "storage")
        self.journal = AppendJournal(self.root / "inventory.log")
        self.inventory = Inventory(self.journal.path)

    def put(self, data: bytes, *, metadata: dict[str, str] | None = None) -> Manifest:
        transaction = StorageTransaction(self)
        manifest = transaction.prepare(data, metadata=metadata)
        transaction.commit()
        self.inventory.load()
        return manifest

    def get(self, object_id: str) -> bytes:
        manifest = self.store.get_manifest(object_id)
        chunks = [self.store.get(chunk_id) for chunk_id in manifest.chunks]
        data = b"".join(chunks)
        if len(data) != manifest.size:
            raise IOError("manifest size mismatch")
        return data

    def audit(self) -> dict[str, object]:
        corrupt: list[str] = []
        for object_id in self.inventory.records:
            try:
                self.get(object_id)
            except (IOError, ValueError):
                corrupt.append(object_id)
        return {"ok": not corrupt, "objects_checked": len(self.inventory.records), "corrupt_objects": corrupt}

    def recover(self) -> dict[str, int]:
        before = len(self.inventory.records)
        self.inventory.load()
        return {"objects_before": before, "objects_after": len(self.inventory.records)}
