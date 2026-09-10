import pytest

from fs_overlay.isolation import IsolationBackend, LinuxNamespaceBackend, WindowsJobObjectBackend
from fs_overlay.lowering import lower_environment
from fs_overlay.model import EnvironmentSpec, ExecutionPolicy


def test_native_lowering_refuses_unenforced_default_policy():
    spec = EnvironmentSpec(name="demo", command=("python", "-c", "print('x')"))
    with pytest.raises(ValueError, match="cannot enforce"):
        lower_environment(spec, IsolationBackend())


def test_native_lowering_preserves_explicit_host_policy():
    spec = EnvironmentSpec(
        name="demo",
        command=("python", "-c", "print('x')"),
        policy=ExecutionPolicy(runtime="native", filesystem="host", network="host"),
        environment={"FS_TEST": "1"},
    )
    lowered = lower_environment(spec, IsolationBackend())
    assert lowered.argv == spec.command
    assert lowered.guarantees == ()
    assert lowered.environment == (("FS_TEST", "1"),)


def test_linux_namespace_lowering_is_explicit():
    spec = EnvironmentSpec(
        name="demo",
        command=("python", "-c", "print('x')"),
        policy=ExecutionPolicy(runtime="linux-namespaces", filesystem="host", network="host"),
    )
    backend = LinuxNamespaceBackend()
    if not backend.plan().available:
        pytest.skip("Linux namespace launcher unavailable")
    lowered = lower_environment(spec, backend)
    assert lowered.argv[-3:] == spec.command
    assert "mount-namespace" in lowered.guarantees
    assert "pid-namespace" in lowered.guarantees


def test_windows_lowering_fails_closed_until_native_binding_exists():
    spec = EnvironmentSpec(
        name="demo",
        command=("example.exe",),
        policy=ExecutionPolicy(runtime="windows-job-objects", filesystem="host", network="host"),
    )
    with pytest.raises(ValueError, match="not implemented"):
        lower_environment(spec, WindowsJobObjectBackend())
