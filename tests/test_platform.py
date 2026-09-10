import platform

from fs_overlay.platform import LinuxPlatformAdapter, WindowsPlatformAdapter, current_platform_adapter


def test_linux_descriptor_is_observational():
    descriptor = LinuxPlatformAdapter().describe()
    assert descriptor.name == "linux"
    assert descriptor.cpu_cores >= 1
    assert set(descriptor.features) == {"namespaces", "cgroups"}


def test_windows_descriptor_declares_job_objects():
    descriptor = WindowsPlatformAdapter().describe()
    assert descriptor.name == "windows"
    assert descriptor.features["job_objects"] is True


def test_current_adapter_matches_host_platform():
    adapter = current_platform_adapter()
    assert adapter.describe().name == platform.system().lower()
