from fs_overlay.backend_capabilities import negotiate_backend_capabilities


def test_linux_capabilities_are_conservative(monkeypatch):
    monkeypatch.setattr("fs_overlay.backend_capabilities.platform.system", lambda: "Linux")
    caps = negotiate_backend_capabilities()
    assert caps.resource_backend == "linux-cgroup-v2"
    assert "cpu_millis" in caps.resources
    assert caps.filesystem_isolation == ("workspace-only",)


def test_windows_capabilities_advertise_only_native_resources(monkeypatch):
    monkeypatch.setattr("fs_overlay.backend_capabilities.platform.system", lambda: "Windows")
    caps = negotiate_backend_capabilities()
    assert caps.resource_backend == "windows-job-object"
    assert caps.resources == ("cpu_millis", "memory_bytes", "pids")
    assert caps.filesystem_isolation == ()


def test_macos_capabilities_fail_closed_without_signed_runtime(monkeypatch):
    monkeypatch.setattr("fs_overlay.backend_capabilities.platform.system", lambda: "Darwin")
    caps = negotiate_backend_capabilities()
    assert caps.resource_backend is None
    assert caps.resources == ()
    assert caps.reasons == ("macos_signed_sandbox_runtime_required",)
