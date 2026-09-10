from fs_overlay.backend_contract import (
    BACKEND_CONTRACT_VERSION,
    LINUX_BUBBLEWRAP_CONTRACT,
    LINUX_CGROUP_V2_CONTRACT,
    WINDOWS_JOB_OBJECT_CONTRACT,
)


def test_backend_contracts_are_versioned():
    assert LINUX_BUBBLEWRAP_CONTRACT.compatible_with()
    assert LINUX_CGROUP_V2_CONTRACT.compatible_with()
    assert WINDOWS_JOB_OBJECT_CONTRACT.compatible_with()


def test_contract_rejects_unknown_version():
    assert not LINUX_CGROUP_V2_CONTRACT.compatible_with(BACKEND_CONTRACT_VERSION + 1)


def test_resource_contracts_advertise_only_verified_types():
    assert LINUX_CGROUP_V2_CONTRACT.resource_types == ("cpu_millis", "memory_bytes", "pids")
    assert WINDOWS_JOB_OBJECT_CONTRACT.resource_types == ("cpu_millis", "memory_bytes", "pids")
    assert "resource-controller-enforced" in WINDOWS_JOB_OBJECT_CONTRACT.evidence_markers
