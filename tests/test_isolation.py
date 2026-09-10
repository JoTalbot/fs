import platform

import pytest

from fs_overlay.isolation import (
    BubblewrapWorkspaceBackend,
    LinuxNamespaceBackend,
    WindowsJobObjectBackend,
    current_isolation_backend,
)


linux_only = pytest.mark.skipif(
    platform.system().lower() != "linux",
    reason="Linux namespace and bubblewrap backend",
)


def test_linux_namespace_backend_is_explicit_and_bounded():
    backend = LinuxNamespaceBackend()
    plan = backend.plan()
    if platform.system().lower() == "linux":
        assert plan.backend == "linux-namespaces"
        assert "mount-namespace" in plan.guarantees
        assert "pid-namespace" in plan.guarantees
    else:
        assert not plan.available


@linux_only
def test_linux_wrap_rejects_empty_argv():
    backend = LinuxNamespaceBackend()
    if not backend.plan().available:
        pytest.skip("Linux unshare backend unavailable on this host")
    with pytest.raises(ValueError):
        backend.wrap(())


@linux_only
def test_bubblewrap_requires_explicit_workspace():
    backend = BubblewrapWorkspaceBackend()
    plan = backend.plan()
    assert not plan.available
    assert plan.reason in {
        "bubblewrap utility is unavailable",
        "bubblewrap version is unknown",
        "workspace_path_required",
    }


@linux_only
def test_bubblewrap_wrap_requires_workspace(tmp_path, monkeypatch):
    backend = BubblewrapWorkspaceBackend()
    monkeypatch.setattr(backend, "_binary", lambda: "/usr/bin/bwrap")
    monkeypatch.setattr(backend, "_version", lambda binary: (0, 12, 0))
    plan = backend.plan(str(tmp_path))
    assert plan.available
    assert "workspace-filesystem-boundary" in plan.guarantees
    wrapped = backend.wrap(("/bin/true",), workspace_path=str(tmp_path))
    assert wrapped[-10:-7] == ("/workspace", "--", "/bin/sh")
    assert wrapped[-7:-4] == ("-c", backend._boundary_script, "fs-boundary")
    assert wrapped[-4] == str(tmp_path)
    assert wrapped[-2:] == ("deny", "/bin/true")
    assert wrapped[-3].startswith("net:[")
    assert "/workspace" in wrapped
    assert "--ro-bind" in wrapped


@linux_only
def test_bubblewrap_supports_writable_workspace(tmp_path, monkeypatch):
    backend = BubblewrapWorkspaceBackend()
    monkeypatch.setattr(backend, "_binary", lambda: "/usr/bin/bwrap")
    monkeypatch.setattr(backend, "_version", lambda binary: (0, 12, 0))
    plan = backend.plan(str(tmp_path), read_only=False)
    assert plan.available
    workspace_index = plan.argv_prefix.index(str(tmp_path))
    assert plan.argv_prefix[workspace_index - 1] == "--bind"


@linux_only
def test_bubblewrap_rejects_workspace_inside_runtime_roots(monkeypatch):
    backend = BubblewrapWorkspaceBackend()
    monkeypatch.setattr(backend, "_binary", lambda: "/usr/bin/bwrap")
    monkeypatch.setattr(backend, "_version", lambda binary: (0, 12, 0))
    plan = backend.plan("/usr/local")
    assert not plan.available
    assert plan.reason == "workspace_path_overlaps_runtime_root"


@linux_only
def test_bubblewrap_preserves_network_policy(tmp_path, monkeypatch):
    backend = BubblewrapWorkspaceBackend()
    monkeypatch.setattr(backend, "_binary", lambda: "/usr/bin/bwrap")
    monkeypatch.setattr(backend, "_version", lambda binary: (0, 12, 0))
    denied = backend.plan(str(tmp_path), network="deny")
    hosted = backend.plan(str(tmp_path), network="host")
    assert "--unshare-net" in denied.argv_prefix
    assert "--unshare-net" not in hosted.argv_prefix


@linux_only
def test_bubblewrap_boundary_script_observes_network_namespace():
    backend = BubblewrapWorkspaceBackend()
    assert "readlink /proc/self/ns/net" in backend._boundary_script
    assert 'network_mode" = "deny' in backend._boundary_script


def test_windows_backend_never_claims_filesystem_or_network_isolation():
    plan = WindowsJobObjectBackend().plan()
    if platform.system().lower() == "windows":
        assert not plan.available
        assert "filesystem/network isolation" in plan.reason
    else:
        assert not plan.available


def test_current_backend_matches_host_family():
    backend = current_isolation_backend()
    system = platform.system().lower()
    if system == "linux":
        assert isinstance(backend, LinuxNamespaceBackend)
    elif system == "windows":
        assert isinstance(backend, WindowsJobObjectBackend)
