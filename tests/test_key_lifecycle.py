import pytest

from fs_overlay.key_lifecycle import KeyLifecycle, KeyRecord


def test_rotation_retires_previous_active_key() -> None:
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    lifecycle.rotate(KeyRecord("k2", "fp2"))
    assert not lifecycle.usable_for_signing("k1")
    assert lifecycle.usable_for_verification("k1")
    assert lifecycle.usable_for_signing("k2")
    assert [record.key_id for record in lifecycle.active()] == ["k2"]


def test_revocation_is_terminal_for_key_use() -> None:
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    lifecycle.revoke("k1")
    assert not lifecycle.usable_for_signing("k1")
    assert not lifecycle.usable_for_verification("k1")


def test_duplicate_key_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate key_id"):
        KeyLifecycle([KeyRecord("k1", "fp1"), KeyRecord("k1", "fp1")])


def test_multiple_active_keys_are_rejected() -> None:
    with pytest.raises(ValueError, match="at most one active"):
        KeyLifecycle([KeyRecord("k1", "fp1"), KeyRecord("k2", "fp2")])


def test_key_id_cannot_change_fingerprint_silently() -> None:
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    with pytest.raises(ValueError, match="cannot change silently"):
        lifecycle.rotate(KeyRecord("k1", "fp2"))


def test_rotation_requires_active_record() -> None:
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    with pytest.raises(ValueError, match="requires an ACTIVE"):
        lifecycle.rotate(KeyRecord("k2", "fp2", "RETIRED"))


def test_fingerprint_lookup_is_deterministic() -> None:
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    assert lifecycle.fingerprint_for("k1") == "fp1"
    assert lifecycle.fingerprint_for("missing") is None


def test_legacy_usable_alias_still_means_signing() -> None:
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    lifecycle.rotate(KeyRecord("k2", "fp2"))
    assert not lifecycle.usable("k1")
    assert lifecycle.usable("k2")
