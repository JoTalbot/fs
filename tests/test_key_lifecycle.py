import pytest

from fs_overlay.key_lifecycle import KeyLifecycle, KeyRecord
from fs_overlay.production_adapters import KeyAdmission, ReferenceKeyLifecycleAdmission


def test_rotation_retires_previous_active_key():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    lifecycle.rotate(KeyRecord("k2", "fp2"))
    assert not lifecycle.usable_for_signing("k1")
    assert lifecycle.usable_for_verification("k1")
    assert lifecycle.usable_for_signing("k2")
    assert [record.key_id for record in lifecycle.active()] == ["k2"]


def test_explicit_retirement_preserves_verification_only():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    lifecycle.retire("k1")
    assert not lifecycle.usable_for_signing("k1")
    assert lifecycle.usable_for_verification("k1")
    lifecycle.retire("k1")
    lifecycle.revoke("k1")
    with pytest.raises(ValueError, match="revoked key cannot be retired"):
        lifecycle.retire("k1")
    with pytest.raises(ValueError, match="key is not admitted"):
        lifecycle.retire("missing")


def test_revocation_is_terminal_for_key_use():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    lifecycle.revoke("k1")
    assert not lifecycle.usable_for_signing("k1")
    assert not lifecycle.usable_for_verification("k1")


def test_duplicate_key_id_is_rejected():
    with pytest.raises(ValueError, match="duplicate key_id"):
        KeyLifecycle([KeyRecord("k1", "fp1"), KeyRecord("k1", "fp1")])


def test_multiple_active_keys_are_rejected():
    with pytest.raises(ValueError, match="at most one active"):
        KeyLifecycle([KeyRecord("k1", "fp1"), KeyRecord("k2", "fp2")])


def test_key_id_cannot_change_fingerprint_silently():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    with pytest.raises(ValueError, match="cannot change silently"):
        lifecycle.rotate(KeyRecord("k1", "fp2"))


def test_rotation_requires_active_record():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    with pytest.raises(ValueError, match="requires an ACTIVE"):
        lifecycle.rotate(KeyRecord("k2", "fp2", "RETIRED"))


def test_fingerprint_lookup_is_deterministic():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    assert lifecycle.fingerprint_for("k1") == "fp1"
    assert lifecycle.fingerprint_for("missing") is None


def test_legacy_usable_alias_still_means_signing():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    lifecycle.rotate(KeyRecord("k2", "fp2"))
    assert not lifecycle.usable("k1")
    assert lifecycle.usable("k2")


def test_reference_lifecycle_adapter_is_a_key_admission_boundary():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    adapter = ReferenceKeyLifecycleAdmission(lifecycle)
    assert isinstance(adapter, KeyAdmission)
    assert adapter.admit_key("node-1", "k1", "fp1")
    assert adapter.is_key_admitted("node-1", "k1", "fp1")
    assert adapter.can_sign("node-1", "k1")
    assert adapter.can_verify("node-1", "k1")


def test_reference_lifecycle_adapter_explicit_retirement():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    adapter = ReferenceKeyLifecycleAdmission(lifecycle)
    assert adapter.admit_key("node-1", "k1", "fp1")
    adapter.retire_key("node-1", "k1")
    assert adapter.is_key_admitted("node-1", "k1", "fp1")
    assert not adapter.can_sign("node-1", "k1")
    assert adapter.can_verify("node-1", "k1")


def test_reference_lifecycle_adapter_rejects_wrong_fingerprint_and_node():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    adapter = ReferenceKeyLifecycleAdmission(lifecycle)
    assert not adapter.admit_key("node-1", "k1", "wrong")
    assert adapter.admit_key("node-1", "k1", "fp1")
    assert not adapter.admit_key("node-2", "k1", "fp1")
    assert not adapter.is_key_admitted("node-2", "k1", "fp1")


def test_reference_lifecycle_adapter_maps_rotation_and_revocation_fail_closed():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    adapter = ReferenceKeyLifecycleAdmission(lifecycle)
    assert adapter.admit_key("node-1", "k1", "fp1")
    lifecycle.rotate(KeyRecord("k2", "fp2"))
    assert not adapter.can_sign("node-1", "k1")
    assert adapter.can_verify("node-1", "k1")
    assert adapter.admit_key("node-1", "k2", "fp2")
    assert adapter.can_sign("node-1", "k2")
    adapter.revoke_key("node-1", "k2", "incident")
    assert not adapter.can_sign("node-1", "k2")
    assert not adapter.can_verify("node-1", "k2")


def test_reference_lifecycle_adapter_rejects_reactivation_after_retirement():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    adapter = ReferenceKeyLifecycleAdmission(lifecycle)
    assert adapter.admit_key("node-1", "k1", "fp1")
    adapter.retire_key("node-1", "k1")
    assert not adapter.admit_key("node-1", "k1", "fp1")
    assert adapter.can_verify("node-1", "k1")
    assert not adapter.can_sign("node-1", "k1")


def test_reference_lifecycle_adapter_unknown_node_revocation_does_not_revoke_key():
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    adapter = ReferenceKeyLifecycleAdmission(lifecycle)
    adapter.revoke_key("node-unknown", "k1", "incident")
    assert adapter.admit_key("node-1", "k1", "fp1")
    assert adapter.can_sign("node-1", "k1")
    assert adapter.can_verify("node-1", "k1")
