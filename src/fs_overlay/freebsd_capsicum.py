"""FreeBSD Capsicum capability-mode adapter.

Capsicum is a capability sandbox, not a drop-in replacement for Linux network
namespaces. This adapter intentionally exposes only the native operation that
can be verified here: entering capability mode in the current process and
reading the kernel mode back. A dedicated helper should call it after opening
all required descriptors and before running untrusted work.
"""
from __future__ import annotations

from dataclasses import dataclass
import ctypes
import platform


@dataclass(frozen=True, slots=True)
class CapsicumResult:
    available: bool
    verified: bool
    evidence: tuple[str, ...] = ()
    reason: str = ""


class FreeBSDCapsicumBackend:
    name = "freebsd-capsicum"

    def plan(self) -> CapsicumResult:
        if platform.system().lower() != "freebsd":
            return CapsicumResult(False, False, reason="host is not FreeBSD")
        return CapsicumResult(True, False, reason="cap_enter requires execution in the workload process")

    def enter_current_process(self) -> CapsicumResult:
        if platform.system().lower() != "freebsd":
            return CapsicumResult(False, False, reason="host is not FreeBSD")
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            cap_enter = libc.cap_enter
            cap_enter.argtypes = []
            cap_enter.restype = ctypes.c_int
            cap_getmode = libc.cap_getmode
            cap_getmode.argtypes = [ctypes.POINTER(ctypes.c_uint)]
            cap_getmode.restype = ctypes.c_int
        except (AttributeError, OSError):
            return CapsicumResult(False, False, reason="Capsicum libc API unavailable")

        if cap_enter() != 0:
            errno = ctypes.get_errno()
            return CapsicumResult(False, False, reason=f"cap_enter_failed:{errno}")

        mode = ctypes.c_uint(0)
        if cap_getmode(ctypes.byref(mode)) != 0 or mode.value != 1:
            return CapsicumResult(False, False, reason="capability_mode_readback_failed")
        return CapsicumResult(
            True,
            True,
            ("capsicum-capability-mode-entered", "capsicum-capability-mode-verified"),
            "native kernel read-back verified",
        )
