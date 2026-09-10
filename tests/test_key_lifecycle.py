from fs_overlay.key_lifecycle import KeyLifecycle, KeyRecord


def test_rotation_retires_previous_active_key() -> None:
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    lifecycle.rotate(KeyRecord("k2", "fp2"))
    assert not lifecycle.usable("k1")
    assert lifecycle.usable("k2")
    assert [record.key_id for record in lifecycle.active()] == ["k2"]


def test_revocation_is_terminal_for_key_use() -> None:
    lifecycle = KeyLifecycle([KeyRecord("k1", "fp1")])
    lifecycle.revoke("k1")
    assert not lifecycle.usable("k1")
