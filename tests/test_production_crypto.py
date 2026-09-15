from __future__ import annotations

import pytest

from fs_overlay.production_crypto import CryptographyAESGCM
import fs_overlay.production_crypto as production_crypto


pytestmark = pytest.mark.crypto_provider


@pytest.fixture
def provider() -> CryptographyAESGCM:
    return CryptographyAESGCM(b"k" * 32)


def test_aes_gcm_round_trip_and_nonce_uniqueness(provider: CryptographyAESGCM) -> None:
    first = provider.encrypt(b"payload", associated_data=b"object:1")
    second = provider.encrypt(b"payload", associated_data=b"object:1")
    assert first != second
    assert len(first) >= provider.nonce_size + provider.tag_size
    assert provider.decrypt(first, associated_data=b"object:1") == b"payload"
    assert provider.decrypt(second, associated_data=b"object:1") == b"payload"


def test_aes_gcm_binds_associated_data(provider: CryptographyAESGCM) -> None:
    from cryptography.exceptions import InvalidTag

    ciphertext = provider.encrypt(b"payload", associated_data=b"object:1")
    with pytest.raises(InvalidTag):
        provider.decrypt(ciphertext, associated_data=b"object:2")


def test_aes_gcm_rejects_ciphertext_tampering(provider: CryptographyAESGCM) -> None:
    from cryptography.exceptions import InvalidTag

    ciphertext = bytearray(provider.encrypt(b"payload"))
    ciphertext[-1] ^= 1
    with pytest.raises(InvalidTag):
        provider.decrypt(bytes(ciphertext))


def test_aes_gcm_rejects_structural_truncation(provider: CryptographyAESGCM) -> None:
    ciphertext = provider.encrypt(b"payload")
    truncated = ciphertext[: provider.nonce_size + provider.tag_size - 1]
    with pytest.raises(ValueError, match="invalid or truncated"):
        provider.decrypt(truncated)


def test_aes_gcm_survives_provider_restart(provider: CryptographyAESGCM) -> None:
    ciphertext = provider.encrypt(b"payload", associated_data=b"object:restart")
    restarted = CryptographyAESGCM(b"k" * 32)
    assert restarted.decrypt(ciphertext, associated_data=b"object:restart") == b"payload"


def test_aes_gcm_key_rotation_keeps_old_data_decryptable_during_migration() -> None:
    from cryptography.exceptions import InvalidTag

    old = CryptographyAESGCM(b"o" * 32)
    new = CryptographyAESGCM(b"n" * 32)
    ciphertext = old.encrypt(b"payload", associated_data=b"object:rotate")

    assert old.decrypt(ciphertext, associated_data=b"object:rotate") == b"payload"
    with pytest.raises(InvalidTag):
        new.decrypt(ciphertext, associated_data=b"object:rotate")

    rotated = new.encrypt(b"payload", associated_data=b"object:rotate")
    assert new.decrypt(rotated, associated_data=b"object:rotate") == b"payload"


def test_aes_gcm_rejects_malformed_envelopes(provider: CryptographyAESGCM) -> None:
    malformed = [b"", b"nonce-only", b"n" * (provider.nonce_size + provider.tag_size - 1)]
    for ciphertext in malformed:
        with pytest.raises(ValueError, match="invalid or truncated"):
            provider.decrypt(ciphertext)


def test_aes_gcm_requires_256_bit_key() -> None:
    with pytest.raises(ValueError, match="32-byte key"):
        CryptographyAESGCM(b"short")
    with pytest.raises(ValueError, match="32-byte key"):
        CryptographyAESGCM(bytearray(b"k" * 32))


@pytest.mark.parametrize(
    ("method", "args"),
    [
        ("encrypt", ("payload",)),
        ("decrypt", ("ciphertext",)),
    ],
)
def test_aes_gcm_rejects_non_bytes_payload(provider: CryptographyAESGCM, method: str, args: tuple[str]) -> None:
    with pytest.raises(TypeError, match="must be bytes"):
        getattr(provider, method)(*args)


def test_aes_gcm_rejects_non_bytes_associated_data(provider: CryptographyAESGCM) -> None:
    with pytest.raises(TypeError, match="associated_data must be bytes"):
        provider.encrypt(b"payload", associated_data="object:1")
    with pytest.raises(TypeError, match="associated_data must be bytes"):
        provider.decrypt(provider.encrypt(b"payload"), associated_data="object:1")


@pytest.mark.parametrize("bad_nonce", [b"", b"short", b"n" * 13])
def test_aes_gcm_rejects_invalid_nonce_source(
    provider: CryptographyAESGCM, monkeypatch: pytest.MonkeyPatch, bad_nonce: bytes
) -> None:
    monkeypatch.setattr(production_crypto.os, "urandom", lambda size: bad_nonce)
    with pytest.raises(RuntimeError, match="invalid AES-GCM nonce"):
        provider.encrypt(b"payload")
