import ctypes
import platform
import subprocess
import sys
from pathlib import Path

import pytest

from fs_overlay.freebsd_capsicum import FreeBSDCapsicumBackend


@pytest.mark.skipif(platform.system().lower() != "freebsd", reason="requires a real FreeBSD kernel")
def test_capsicum_native_entrypoint_round_trip_in_child_process():
    code = """
from fs_overlay.freebsd_capsicum import FreeBSDCapsicumBackend
result = FreeBSDCapsicumBackend().enter_current_process()
assert result.available
assert result.verified
assert "capsicum-capability-mode-entered" in result.evidence
assert "capsicum-capability-mode-verified" in result.evidence
print(result.reason)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert "native kernel read-back verified" in completed.stdout


@pytest.mark.skipif(platform.system().lower() != "freebsd", reason="requires a real FreeBSD kernel")
def test_capsicum_exec_helper_compiles_and_replaces_itself(tmp_path: Path):
    source = Path("native/freebsd/capsicum_exec.c")
    helper = tmp_path / "capsicum_exec"
    compiled = subprocess.run(
        ["cc", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(helper)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert compiled.returncode == 0, compiled.stderr

    completed = subprocess.run(
        [str(helper), "/bin/echo", "capsicum-helper-ok"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "capsicum-helper-ok\n"
    assert "capsicum-capability-mode-entered" in completed.stderr
    assert "capsicum-capability-mode-verified" in completed.stderr
    assert "capsicum-global-namespace-blocked" in completed.stderr


def test_capsicum_is_fail_closed_off_platform(monkeypatch):
    monkeypatch.setattr("fs_overlay.freebsd_capsicum.platform.system", lambda: "Linux")
    result = FreeBSDCapsicumBackend().plan()
    assert not result.available
    assert not result.verified
    assert result.reason == "host is not FreeBSD"


def test_capsicum_does_not_claim_execution_evidence_during_planning(monkeypatch):
    monkeypatch.setattr("fs_overlay.freebsd_capsicum.platform.system", lambda: "FreeBSD")
    result = FreeBSDCapsicumBackend().plan()
    assert result.available
    assert not result.verified
    assert result.reason == "cap_enter requires execution in the workload process"


def test_capsicum_native_entrypoint_is_not_used_off_platform(monkeypatch):
    monkeypatch.setattr("fs_overlay.freebsd_capsicum.platform.system", lambda: "Linux")
    result = FreeBSDCapsicumBackend().enter_current_process()
    assert not result.available
    assert not result.verified
    assert result.reason == "host is not FreeBSD"


class _FakeCFunction:
    def __init__(self, implementation):
        self.implementation = implementation
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.implementation(*args)


class _FakeLibc:
    def __init__(self, cap_enter, cap_getmode):
        self.cap_enter = _FakeCFunction(cap_enter)
        self.cap_getmode = _FakeCFunction(cap_getmode)


def _fake_freebsd(monkeypatch, libc):
    monkeypatch.setattr("fs_overlay.freebsd_capsicum.platform.system", lambda: "FreeBSD")
    monkeypatch.setattr("fs_overlay.freebsd_capsicum.ctypes.CDLL", lambda *args, **kwargs: libc)


def test_capsicum_handles_missing_libc_api(monkeypatch):
    monkeypatch.setattr("fs_overlay.freebsd_capsicum.platform.system", lambda: "FreeBSD")

    class MissingLibc:
        cap_enter = _FakeCFunction(lambda: 0)

    monkeypatch.setattr("fs_overlay.freebsd_capsicum.ctypes.CDLL", lambda *args, **kwargs: MissingLibc())
    result = FreeBSDCapsicumBackend().enter_current_process()
    assert not result.available
    assert not result.verified
    assert result.reason == "Capsicum libc API unavailable"


def test_capsicum_reports_cap_enter_errno(monkeypatch):
    libc = _FakeLibc(lambda: -1, lambda pointer: 0)
    _fake_freebsd(monkeypatch, libc)
    monkeypatch.setattr("fs_overlay.freebsd_capsicum.ctypes.get_errno", lambda: 77)

    result = FreeBSDCapsicumBackend().enter_current_process()
    assert not result.available
    assert not result.verified
    assert result.reason == "cap_enter_failed:77"


def test_capsicum_handles_cap_getmode_failure(monkeypatch):
    libc = _FakeLibc(lambda: 0, lambda pointer: -1)
    _fake_freebsd(monkeypatch, libc)

    result = FreeBSDCapsicumBackend().enter_current_process()
    assert not result.available
    assert not result.verified
    assert result.reason == "capability_mode_readback_failed"


def test_capsicum_handles_unverified_capability_mode(monkeypatch):
    def cap_getmode(pointer):
        pointer._obj.value = 0
        return 0

    libc = _FakeLibc(lambda: 0, cap_getmode)
    _fake_freebsd(monkeypatch, libc)

    result = FreeBSDCapsicumBackend().enter_current_process()
    assert not result.available
    assert not result.verified
    assert result.reason == "capability_mode_readback_failed"
