"""Candidate production AEAD provider using ``cryptography`` AES-GCM.

This adapter is intentionally opt-in. It provides a concrete implementation of
FS's ``AuthenticatedEncryption`` protocol, but its presence is not evidence of
an external security audit or of a deployment-specific key-management review.
"""
from __future__ import annotations

import os

from .storage_engine import AuthenticatedEncryption


class CryptographyAESGCM(AuthenticatedEncryption):
    """AES-256-GCM adapter with a random 96-bit nonce per encryption.

    The serialized envelope is ``nonce || AESGCM(ciphertext+tag)``. A fresh
    nonce is generated for every call, and AAD is passed directly to GCM.
    """

    name = "cryptography-aes-256-gcm"
    nonce_size = 12
    key_size = 32
    tag_size = 16

    def __init__(self, key: bytes):
        if not isinstance(key, bytes) or len(key) != self.key_size:
            raise ValueError("AES-256-GCM requires a 32-byte key")
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError(
                "cryptography is required for CryptographyAESGCM; install the crypto extra"
            ) from exc
        self._aesgcm = AESGCM(key)

    @staticmethod
    def _require_bytes(value: bytes, field: str) -> None:
        if not isinstance(value, bytes):
            raise TypeError(f"{field} must be bytes")

    def encrypt(self, plaintext: bytes, *, associated_data: bytes = b"") -> bytes:
        self._require_bytes(plaintext, "plaintext")
        self._require_bytes(associated_data, "associated_data")
        nonce = os.urandom(self.nonce_size)
        if not isinstance(nonce, bytes) or len(nonce) != self.nonce_size:
            raise RuntimeError("nonce source returned an invalid AES-GCM nonce")
        return nonce + self._aesgcm.encrypt(nonce, plaintext, associated_data)

    def decrypt(self, ciphertext: bytes, *, associated_data: bytes = b"") -> bytes:
        self._require_bytes(ciphertext, "ciphertext")
        self._require_bytes(associated_data, "associated_data")
        if len(ciphertext) < self.nonce_size + self.tag_size:
            raise ValueError("invalid or truncated AES-GCM envelope")
        nonce = ciphertext[: self.nonce_size]
        payload = ciphertext[self.nonce_size :]
        if len(payload) < self.tag_size:
            raise ValueError("invalid or truncated AES-GCM envelope")
        return self._aesgcm.decrypt(nonce, payload, associated_data)
