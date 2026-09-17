"""Crash-safe local persistence for the node identity descriptor.

The store persists only public identity metadata. Private key material remains
outside the filesystem core and must be supplied by a separately qualified
secure key store.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile

from .identity import NodeIdentity


SCHEMA_VERSION = 1


def _validate_identity(identity: NodeIdentity) -> None:
    if not isinstance(identity.node_id, str) or not identity.node_id:
        raise ValueError("invalid node identity: node id must be a non-empty string")
    if not isinstance(identity.public_key_fingerprint, str):
        raise ValueError("invalid node identity: fingerprint must be a string")
    if len(identity.public_key_fingerprint) != 64:
        raise ValueError("invalid node identity: fingerprint must be SHA-256")
    try:
        int(identity.public_key_fingerprint, 16)
    except ValueError as exc:
        raise ValueError("invalid node identity: fingerprint is not hexadecimal") from exc
    if not isinstance(identity.protocol_version, str) or not identity.protocol_version:
        raise ValueError("invalid node identity: protocol version must be a non-empty string")


class LocalNodeIdentityStore:
    """Persist and recover a single :class:`NodeIdentity` atomically."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> NodeIdentity | None:
        """Return the persisted identity, or ``None`` when no file exists."""
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        try:
            document = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("invalid node identity store encoding") from exc
        if not isinstance(document, dict) or type(document.get("schema_version")) is not int:
            raise ValueError("invalid node identity store schema")
        if document["schema_version"] != SCHEMA_VERSION:
            raise ValueError("unsupported node identity store schema")
        identity_data = document.get("identity")
        if not isinstance(identity_data, dict):
            raise ValueError("invalid node identity store identity")
        try:
            identity = NodeIdentity(
                node_id=identity_data["node_id"],
                public_key_fingerprint=identity_data["public_key_fingerprint"],
                protocol_version=identity_data["protocol_version"],
            )
        except (KeyError, TypeError) as exc:
            raise ValueError("invalid node identity store identity") from exc
        try:
            _validate_identity(identity)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid node identity store identity") from exc
        return identity

    def save(self, identity: NodeIdentity) -> None:
        """Atomically replace the identity file and durably flush the directory."""
        _validate_identity(identity)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "schema_version": SCHEMA_VERSION,
            "identity": asdict(identity),
        }
        payload = json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            try:
                os.fchmod(fd, 0o600)
            except (AttributeError, OSError):
                pass
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                fd = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            try:
                directory_fd = os.open(self.path.parent, os.O_RDONLY)
            except OSError:
                directory_fd = None
            if directory_fd is not None:
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        finally:
            if fd != -1:
                os.close(fd)
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
