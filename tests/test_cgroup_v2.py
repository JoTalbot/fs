from fs_overlay.cgroup_v2 import LinuxCgroupV2Backend
from fs_overlay.model import ResourceBudget
from fs_overlay.resource_control import ResourceLease


def delegated_scope(tmp_path):
    (tmp_path / "cgroup.controllers").write_text("cpu memory pids\n", encoding="ascii")
    (tmp_path / "cgroup.procs").write_text("\n", encoding="ascii")
    (tmp_path / "cpu.max").write_text("max 100000\n", encoding="ascii")
    (tmp_path / "memory.max").write_text("max\n", encoding="ascii")
    (tmp_path / "pids.max").write_text("max\n", encoding="ascii")
    return tmp_path


def lease_for(path):
    return ResourceLease("lease-1", str(path), "fs")


def test_cgroup_plan_requires_explicit_lease(tmp_path):
    backend = LinuxCgroupV2Backend()
    plan = backend.plan(None, ResourceBudget(memory_bytes=1024))
    assert not plan.enforceable
    assert "resource_lease_required" in plan.reasons


def test_cgroup_plan_requires_real_v2_scope(monkeypatch, tmp_path):
    backend = LinuxCgroupV2Backend()
    monkeypatch.setattr("fs_overlay.cgroup_v2.platform.system", lambda: "Linux")
    plan = backend.plan(lease_for(tmp_path), ResourceBudget(memory_bytes=1024))
    assert not plan.enforceable
    assert "cgroup_v2_scope_not_detected" in plan.reasons


def test_cgroup_plan_is_explicit_and_scoped(monkeypatch, tmp_path):
    backend = LinuxCgroupV2Backend()
    scope = delegated_scope(tmp_path)
    monkeypatch.setattr("fs_overlay.cgroup_v2.platform.system", lambda: "Linux")
    plan = backend.plan(
        lease_for(scope),
        ResourceBudget(cpu_millis=500, memory_bytes=1024 * 1024, pids=8),
    )
    assert plan.available
    assert plan.enforceable
    assert plan.scope == str(scope)
    assert ("cpu.max", "50000 100000") in plan.settings
    assert ("memory.max", "1048576") in plan.settings
    assert ("pids.max", "8") in plan.settings


def test_cgroup_apply_writes_and_reads_back_exact_limits(monkeypatch, tmp_path):
    backend = LinuxCgroupV2Backend()
    scope = delegated_scope(tmp_path)
    monkeypatch.setattr("fs_overlay.cgroup_v2.platform.system", lambda: "Linux")
    result = backend.apply(
        1234,
        lease_for(scope),
        ResourceBudget(cpu_millis=250, memory_bytes=4096, pids=4),
    )
    assert result.applied
    assert result.verified
    assert (scope / "cpu.max").read_text(encoding="ascii").strip() == "25000 100000"
    assert (scope / "memory.max").read_text(encoding="ascii").strip() == "4096"
    assert (scope / "pids.max").read_text(encoding="ascii").strip() == "4"
    assert (scope / "cgroup.procs").read_text(encoding="ascii").strip() == "1234"


def test_cgroup_rejects_unsupported_disk_limit(monkeypatch, tmp_path):
    backend = LinuxCgroupV2Backend()
    scope = delegated_scope(tmp_path)
    monkeypatch.setattr("fs_overlay.cgroup_v2.platform.system", lambda: "Linux")
    plan = backend.plan(lease_for(scope), ResourceBudget(disk_bytes=1024))
    assert not plan.enforceable
    assert "disk_bytes is not supported by cgroup v2 resource controllers" in plan.reasons


def test_cgroup_rejects_symlink_scope(monkeypatch, tmp_path):
    backend = LinuxCgroupV2Backend()
    scope = delegated_scope(tmp_path / "real")
    link = tmp_path / "link"
    link.symlink_to(scope, target_is_directory=True)
    monkeypatch.setattr("fs_overlay.cgroup_v2.platform.system", lambda: "Linux")
    plan = backend.plan(lease_for(link), ResourceBudget(memory_bytes=1024))
    assert not plan.enforceable
    assert "resource lease scope must not be a symlink" in plan.reasons
