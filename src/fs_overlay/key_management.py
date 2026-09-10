"""Explicit key-management boundary for federation cryptography."""
from __future__ import annotations

from typing import Protocol


class FederationSigner(Protocol):
    def sign(self, payload: bytes, key_id: str) -> bytes: ...
    def verify(self, payload: bytes, signature: bytes, key_id: str) -> bool: ...


class KeyProvider(Protocol):
    def active_key_id(self, node_id: str) -> str: ...
    def public_key_fingerprint(self, key_id: str) -> str: ...
