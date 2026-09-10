"""Small persistent-free node identity primitives for the reference engine."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True, slots=True)
class NodeIdentity:
    node_id: str
    public_key_fingerprint: str
    protocol_version: str = "1"

    @classmethod
    def from_public_key(cls, node_id: str, public_key: bytes, protocol_version: str = "1") -> "NodeIdentity":
        if not node_id:
            raise ValueError("node id is required")
        if not public_key:
            raise ValueError("public key is required")
        fingerprint = hashlib.sha256(public_key).hexdigest()
        return cls(node_id, fingerprint, protocol_version)

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.node_id:
            errors.append("missing node id")
        if len(self.public_key_fingerprint) != 64:
            errors.append("invalid public key fingerprint")
        if not self.protocol_version:
            errors.append("missing protocol version")
        return tuple(errors)
