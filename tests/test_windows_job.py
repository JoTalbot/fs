from fs_overlay.model import ResourceBudget
from fs_overlay.resource_control import ResourceLease
from fs_overlay.windows_job import WindowsJobObjectBackend


def lease():
    return ResourceLease("lease-1", "scope-1", "fs")


def test_windows_backend_is_fail_closed_off_windows():
    plan = WindowsJobObjectBackend().plan(lease(), ResourceBudget(memory_bytes=1024))
    assert not plan.enforceable
    assert "windows_required" in plan.reasons


def test_windows_backend_requires_lease_on_windows(monkeypatch):
    monkeypatch.setattr("fs_overlay.windows_job.os.name", "nt")
    plan = WindowsJobObjectBackend().plan(None, ResourceBudget(memory_bytes=1024))
    assert not plan.enforceable
    assert plan.reasons == ("resource_lease_required",)


def test_windows_backend_rejects_invalid_lease_on_windows(monkeypatch):
    monkeypatch.setattr("fs_overlay.windows_job.os.name", "nt")
    plan = WindowsJobObjectBackend().plan(
        ResourceLease("", "scope-1", "fs"), ResourceBudget(memory_bytes=1024)
    )
    assert not plan.enforceable
    assert "lease_id is required" in plan.reasons


def test_windows_disk_limit_is_explicitly_unsupported_on_windows(monkeypatch):
    monkeypatch.setattr("fs_overlay.windows_job.os.name", "nt")
    plan = WindowsJobObjectBackend().plan(lease(), ResourceBudget(disk_bytes=1024))
    assert not plan.enforceable
    assert "disk_limit_unsupported" in plan.reasons


def test_windows_supported_budget_is_planned_on_windows(monkeypatch):
    monkeypatch.setattr("fs_overlay.windows_job.os.name", "nt")
    plan = WindowsJobObjectBackend().plan(
        lease(), ResourceBudget(cpu_millis=500, memory_bytes=1024, pids=4)
    )
    assert plan.available
    assert plan.enforceable
    assert plan.settings == {"cpu_millis": 500, "memory_bytes": 1024, "pids": 4}
