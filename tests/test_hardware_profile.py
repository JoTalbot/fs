import json

from fs_overlay.hardware_profile import HardwareCapabilityAdapter, HardwareProfile, hardware_capability_fingerprint


def test_hardware_profile_is_stable_and_non_identifying():
    profile = HardwareProfile("x86_64", 8, 16 * 1024**3, {"acceleration": True})
    data = profile.to_dict()
    assert data == {
        "architecture": "x86_64",
        "cpu_cores": 8,
        "memory_bytes": 16 * 1024**3,
        "features": {"acceleration": True},
    }
    assert "serial" not in json.dumps(data).lower()


def test_hardware_capability_fingerprint_is_deterministic():
    first = HardwareProfile("x86_64", 8, 1024, {"b": False, "a": True})
    second = HardwareProfile("x86_64", 8, 1024, {"a": True, "b": False})
    assert hardware_capability_fingerprint(first) == hardware_capability_fingerprint(second)
    assert len(hardware_capability_fingerprint(first)) == 64


def test_hardware_capability_fingerprint_changes_with_capability():
    base = HardwareProfile("x86_64", 8, 1024, {})
    changed = HardwareProfile("x86_64", 16, 1024, {})
    assert hardware_capability_fingerprint(base) != hardware_capability_fingerprint(changed)


def test_hardware_adapter_returns_conservative_profile():
    profile = HardwareCapabilityAdapter().describe()
    assert profile.architecture
    assert profile.cpu_cores >= 1
    assert profile.memory_bytes is None or profile.memory_bytes > 0
