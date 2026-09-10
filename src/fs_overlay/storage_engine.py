"""Dependency-free local FS storage engine foundation."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator, Protocol

FORMAT_VERSION = 1
DEFAULT_CHUNK_SIZE = 1024 * 1024


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


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

    @classmethod
    def from_bytes(cls, data: bytes) -> "Manifest":
        raw = json.loads(data)
        if raw.get("format_version") != FORMAT_VERSION:
            raise ValueError("unsupported manifest format version")
        result = cls(str(raw["object_id"]), int(raw["size"]), tuple(raw["chunks"]),
                     int(raw["chunk_size"]), int(raw["format_version"]), raw.get("metadata"))
        if result.identity() != result.object_id:
            raise ValueError("manifest identity verification failed")
        return result


class DeterministicChunker:
    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE):
        if chunk_size <= 0: raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size
    def split(self, data: bytes) -> Iterator[bytes]:
        for offset in range(0, len(data), self.chunk_size): yield data[offset:offset + self.chunk_size]
    def split_stream(self, stream: BinaryIO) -> Iterator[bytes]:
        while chunk := stream.read(self.chunk_size): yield chunk


class AuthenticatedEncryption(Protocol):
    """Provider boundary. Production deployments must supply audited AEAD."""
    name: str
    def encrypt(self, plaintext: bytes, *, associated_data: bytes = b"") -> bytes: ...
    def decrypt(self, ciphertext: bytes, *, associated_data: bytes = b"") -> bytes: ...


class HMACIntegrityEnvelope:
    """Integrity-only development envelope; it provides no confidentiality."""
    name = "hmac-integrity-envelope"
    def __init__(self, key: bytes):
        if len(key) < 16: raise ValueError("integrity key must be at least 16 bytes")
        self._key = key
    def encrypt(self, plaintext: bytes, *, associated_data: bytes = b"") -> bytes:
        return hmac.new(self._key, associated_data + plaintext, hashlib.sha256).digest() + plaintext
    def decrypt(self, ciphertext: bytes, *, associated_data: bytes = b"") -> bytes:
        if len(ciphertext) < 32: raise ValueError("invalid integrity envelope")
        tag, plaintext = ciphertext[:32], ciphertext[32:]
        expected = hmac.new(self._key, associated_data + plaintext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected): raise ValueError("integrity verification failed")
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
        self.root = Path(root); self.objects = self.root / "objects"; self.manifests = self.root / "manifests"
        self.objects.mkdir(parents=True, exist_ok=True); self.manifests.mkdir(parents=True, exist_ok=True)
    @staticmethod
    def object_id(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
    def _path(self, object_id: str) -> Path:
        if len(object_id) != 64 or any(c not in "0123456789abcdef" for c in object_id): raise ValueError("invalid object id")
        directory = self.objects / object_id[:2]; directory.mkdir(exist_ok=True); return directory / object_id
    def put(self, data: bytes) -> str:
        oid = self.object_id(data); target = self._path(oid)
        if target.exists():
            if self.object_id(target.read_bytes()) != oid: raise IOError("object collision or corruption")
            return oid
        fd, temporary = tempfile.mkstemp(prefix=".tmp-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data); handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
        return oid
    def get(self, object_id: str) -> bytes:
        data = self._path(object_id).read_bytes()
        if self.object_id(data) != object_id: raise IOError("object integrity check failed")
        return data
    def put_manifest(self, manifest: Manifest) -> str:
        if manifest.identity() != manifest.object_id: raise ValueError("manifest identity does not match")
        target = self.manifests / manifest.object_id
        if not target.exists():
            fd, temporary = tempfile.mkstemp(prefix=".tmp-", dir=self.manifests)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(manifest.to_bytes()); handle.flush(); os.fsync(handle.fileno())
                os.replace(temporary, target)
            finally:
                if os.path.exists(temporary): os.unlink(temporary)
        return manifest.object_id
    def get_manifest(self, object_id: str) -> Manifest:
        return Manifest.from_bytes((self.manifests / object_id).read_bytes())


class AppendJournal:
    """Length-prefixed JSON journal; malformed/truncated tail records are ignored on replay."""
    def __init__(self, path: str | Path): self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
    def append(self, operation: str, payload: dict[str, object]) -> dict[str, object]:
        record = {"version": FORMAT_VERSION, "operation": operation, "payload": payload}; encoded = _canonical(record)
        with self.path.open("ab") as handle:
            handle.write(f"{len(encoded):016x}".encode() + encoded + b"\n"); handle.flush(); os.fsync(handle.fileno())
        return record
    def replay(self) -> Iterator[dict[str, object]]:
        if not self.path.exists(): return
        with self.path.open("rb") as handle:
            for line in handle:
                if len(line) < 17: continue
                try:
                    size, body = int(line[:16], 16), line[16:-1]
                    if len(body) != size: continue
                    record = json.loads(body)
                    if record.get("version") == FORMAT_VERSION: yield record
                except (ValueError, json.JSONDecodeError): continue


class Inventory:
    def __init__(self, path: str | Path): self.path = Path(path); self.records: dict[str, ObjectRecord] = {}; self.load()
    def load(self) -> None:
        self.records.clear()
        for record in AppendJournal(self.path).replay():
            payload = record["payload"]; oid = str(payload["object_id"])
            if record["operation"] == "commit": self.records[oid] = ObjectRecord(oid, int(payload["size"]), str(payload["manifest_path"]))
            elif record["operation"] == "delete": self.records.pop(oid, None)


class MerkleDAG:
    @staticmethod
    def leaf(value: bytes) -> str: return hashlib.sha256(b"leaf:" + value).hexdigest()
    @staticmethod
    def parent(children: Iterable[str]) -> str:
        ordered = tuple(children)
        if not ordered: raise ValueError("Merkle parent requires children")
        return hashlib.sha256(b"node:" + _canonical(ordered)).hexdigest()
    @classmethod
    def root(cls, leaves: Iterable[str]) -> str:
        level = list(leaves)
        if not level: return cls.leaf(b"")
        while len(level) > 1: level = [cls.parent(level[i:i + 2]) for i in range(0, len(level), 2)]
        return level[0]


class LocalStorageEngine:
    def __init__(self, root: str | Path, *, chunk_size: int = DEFAULT_CHUNK_SIZE):
        self.root = Path(root); self.store = ContentAddressedStore(self.root); self.journal = AppendJournal(self.root / "journal.log")
        self.inventory = Inventory(self.root / "inventory.log"); self.chunker = DeterministicChunker(chunk_size)
    def put(self, data: bytes, *, metadata: dict[str, str] | None = None) -> Manifest:
        chunks = tuple(self.store.put(chunk) for chunk in self.chunker.split(data))
        unsigned = Manifest("", len(data), chunks, self.chunker.chunk_size, metadata=metadata)
        manifest = Manifest(unsigned.identity(), unsigned.size, unsigned.chunks, unsigned.chunk_size, unsigned.format_version, unsigned.metadata)
        self.store.put_manifest(manifest)
        if manifest.object_id not in self.inventory.records:
            payload = {"object_id": manifest.object_id, "size": manifest.size, "manifest_path": manifest.object_id}
            self.journal.append("commit", payload); self.inventory.records[manifest.object_id] = ObjectRecord(manifest.object_id, manifest.size, manifest.object_id)
        return manifest
    def get(self, object_id: str) -> bytes:
        manifest = self.store.get_manifest(object_id); data = b"".join(self.store.get(chunk) for chunk in manifest.chunks)
        if len(data) != manifest.size or manifest.identity() != object_id: raise IOError("object verification failed")
        return data
    def audit(self) -> dict[str, object]:
        corrupt = []
        for oid in self.inventory.records:
            try: self.get(oid)
            except (OSError, ValueError, IOError): corrupt.append(oid)
        return {"ok": not corrupt, "objects_checked": len(self.inventory.records), "corrupt_objects": corrupt}
    def recover(self) -> dict[str, object]:
        before = len(self.inventory.records); self.inventory.load()
        return {"ok": True, "objects_before": before, "objects_after": len(self.inventory.records), "journal": str(self.journal.path)}


class StorageTransaction:
    """Prepare/commit facade; physical objects are immutable, metadata is journaled last."""
    def __init__(self, engine: LocalStorageEngine): self.engine = engine; self._prepared: list[Manifest] = []
    def prepare(self, data: bytes, *, metadata: dict[str, str] | None = None) -> Manifest:
        manifest = self.engine.put(data, metadata=metadata); self._prepared.append(manifest); return manifest
    def commit(self) -> tuple[Manifest, ...]: result = tuple(self._prepared); self._prepared.clear(); return result
    def rollback(self) -> None: self._prepared.clear()
