from __future__ import annotations

import pytest

from fs_overlay.production_crypto import CryptographyAESGCM


@pytest.fixture
def provider() -> CryptographyAESGCM:
    return CryptographyAESGCM(b"k" * 32)


def test_aes_gcm_round_trip_and_nonce_uniqueness(provider: CryptographyAESGCM) -> None:
    first = provider.encrypt(b"payload", associated_data=b"object:1")
    second = provider.encrypt(b"payload", associated_data=b"object:1")
    assert first != second
    assert len(first) >= provider.nonce_size + 16
    assert provider.decrypt(first, associated_data=b"object:1") == b"payload"
    assert provider.decrypt(second, associated_data=b"object:1") == b"payload"


def test_aes_gcm_binds_associated_data(provider: CryptographyAESGCM) -> None:
    ciphertext = provider.encrypt(b"payload", associated_data=b"object:1")
    with pytest.raises(Exception):
        provider.decrypt(ciphertext, associated_data=b"object:2")


def test_aes_gcm_rejects_ciphertext_tampering(provider: CryptographyAESGCM) -> None:
    ciphertext = bytearray(provider.encrypt(b"payload"))
    ciphertext[-1] ^= 1
    with pytest.raises(Exception):
        provider.decrypt(bytes(ciphertext))


def test_aes_gcm_rejects_truncation(provider: CryptographyAESGCM) -> None:
    ciphertext = provider.encrypt(b"payload")
    with pytest.raises(ValueError, match="invalid or truncated"):
        provider.decrypt(ciphertext[:-1])


def test_aes_gcm_requires_256_bit_key() -> None:
    with pytest.raises(ValueError, match="32-byte key"):
        CryptographyAESGCM(b"short")
