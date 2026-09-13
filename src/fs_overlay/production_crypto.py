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

    def __init__(self, key: bytes):
        if len(key) != self.key_size:
            raise ValueError("AES-256-GCM requires a 32-byte key")
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError(
                "cryptography is required for CryptographyAESGCM; install the crypto extra"
            ) from exc
        self._aesgcm = AESGCM(key)

    def encrypt(self, plaintext: bytes, *, associated_data: bytes = b"") -> bytes:
        nonce = os.urandom(self.nonce_size)
        return nonce + self._aesgcm.encrypt(nonce, plaintext, associated_data)

    def decrypt(self, ciphertext: bytes, *, associated_data: bytes = b"") -> bytes:
        if len(ciphertext) < self.nonce_size + 16:
            raise ValueError("invalid or truncated AES-GCM envelope")
        nonce = ciphertext[: self.nonce_size]
        payload = ciphertext[self.nonce_size :]
        return self._aesgcm.decrypt(nonce, payload, associated_data)
