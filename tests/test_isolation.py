import platform

import pytest

from fs_overlay.isolation import LinuxNamespaceBackend, WindowsJobObjectBackend, current_isolation_backend


def test_linux_namespace_backend_is_explicit_and_bounded():
    backend = LinuxNamespaceBackend()
    plan = backend.plan()
    if platform.system().lower() == "linux":
        assert plan.backend == "linux-namespaces"
        assert "mount-namespace" in plan.guarantees
        assert "pid-namespace" in plan.guarantees
    else:
        assert not plan.available


def test_linux_wrap_rejects_empty_argv():
    backend = LinuxNamespaceBackend()
    if not backend.plan().available:
        pytest.skip("Linux unshare backend unavailable on this host")
    with pytest.raises(ValueError):
        backend.wrap(())


def test_windows_backend_never_claims_implemented_binding():
    plan = WindowsJobObjectBackend().plan()
    if platform.system().lower() == "windows":
        assert not plan.available
        assert "not yet implemented" in plan.reason
    else:
        assert not plan.available


def test_current_backend_matches_host_family():
    backend = current_isolation_backend()
    system = platform.system().lower()
    if system == "linux":
        assert isinstance(backend, LinuxNamespaceBackend)
    elif system == "windows":
        assert isinstance(backend, WindowsJobObjectBackend)
