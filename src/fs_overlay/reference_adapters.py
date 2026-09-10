"""Small deterministic reference adapters for development and conformance tests.

These adapters are intentionally local-only and are NOT production security
implementations. Production deployments must replace them with audited crypto,
secure key storage, authenticated transport, and authoritative admission.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import hmac


class HmacReferenceSigner:
    """Deterministic HMAC signer for local protocol tests only."""

    def __init__(self, keys: dict[str, bytes]):
        self._keys = dict(keys)

    def sign(self, payload: bytes, key_id: str) -> bytes:
        key = self._keys.get(key_id)
        if key is None:
            raise KeyError(key_id)
        return hmac.new(key, payload, hashlib.sha256).digest()

    def verify(self, payload: bytes, signature: bytes, key_id: str) -> bool:
        key = self._keys.get(key_id)
        if key is None:
            return False
        return hmac.compare_digest(hmac.new(key, payload, hashlib.sha256).digest(), signature)


class MemoryKeyProvider:
    """Explicit in-memory key provider for tests; never persists secrets."""

    def __init__(self, keys: dict[str, bytes], active_by_node: dict[str, str]):
        self._keys = dict(keys)
        self._active_by_node = dict(active_by_node)

    def active_key_id(self, node_id: str) -> str:
        return self._active_by_node[node_id]

    def public_key_fingerprint(self, key_id: str) -> str:
        key = self._keys[key_id]
        return hashlib.sha256(key).hexdigest()


@dataclass
class InMemoryNodeAdmission:
    """Explicit allowlist suitable only for local conformance tests."""

    admitted: dict[str, str] = field(default_factory=dict)
    revoked: set[str] = field(default_factory=set)

    def admit(self, node_id: str, public_key_fingerprint: str) -> bool:
        if not node_id or not public_key_fingerprint or node_id in self.revoked:
            return False
        self.admitted[node_id] = public_key_fingerprint
        return True

    def revoke(self, node_id: str, reason: str = "") -> None:
        self.admitted.pop(node_id, None)
        self.revoked.add(node_id)

    def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool:
        return node_id not in self.revoked and self.admitted.get(node_id) == public_key_fingerprint
