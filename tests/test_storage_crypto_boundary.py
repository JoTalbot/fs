from __future__ import annotations

import hashlib
import hmac

import pytest

from fs_overlay.storage_engine import AuthenticatedEncryption


class ContractAEAD:
    """Deterministic test double used only to qualify the provider contract.

    This is intentionally not a cryptographic implementation and must never be
    treated as evidence that production confidentiality is implemented.
    """

    name = "test-contract-aead"

    def __init__(self, key: bytes):
        self._key = key

    def encrypt(self, plaintext: bytes, *, associated_data: bytes = b"") -> bytes:
        tag = hmac.new(self._key, associated_data + plaintext, hashlib.sha256).digest()
        return tag + plaintext

    def decrypt(self, ciphertext: bytes, *, associated_data: bytes = b"") -> bytes:
        if len(ciphertext) < hashlib.sha256().digest_size:
            raise ValueError("invalid ciphertext")
        tag, plaintext = ciphertext[:32], ciphertext[32:]
        expected = hmac.new(self._key, associated_data + plaintext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            raise ValueError("authentication failed")
        return plaintext


def test_provider_boundary_is_runtime_checkable() -> None:
    provider: AuthenticatedEncryption = ContractAEAD(b"k" * 32)
    assert provider.name
    assert provider.decrypt(provider.encrypt(b"payload")) == b"payload"


def test_aead_contract_binds_associated_data() -> None:
    provider: AuthenticatedEncryption = ContractAEAD(b"k" * 32)
    ciphertext = provider.encrypt(b"payload", associated_data=b"manifest:1")
    with pytest.raises(ValueError, match="authentication failed"):
        provider.decrypt(ciphertext, associated_data=b"manifest:2")


def test_aead_contract_rejects_ciphertext_tampering() -> None:
    provider: AuthenticatedEncryption = ContractAEAD(b"k" * 32)
    ciphertext = bytearray(provider.encrypt(b"payload"))
    ciphertext[-1] ^= 1
    with pytest.raises(ValueError, match="authentication failed"):
        provider.decrypt(bytes(ciphertext))


def test_aead_contract_rejects_truncated_ciphertext() -> None:
    provider: AuthenticatedEncryption = ContractAEAD(b"k" * 32)
    with pytest.raises(ValueError, match="invalid ciphertext"):
        provider.decrypt(b"short")
