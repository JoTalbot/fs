"""Native Windows Job Object resource backend.

The backend is Windows-only and fail-closed. Each admitted execution gets its
own Job Object; no host-wide policy is created or modified. CPU, memory and
active-process limits are applied with Win32 Job Object APIs and verified by
querying the configured limits before the process is allowed to continue.
"""
from __future__ import annotations

from dataclasses import dataclass
import ctypes
import os
from typing import Any

from .model import ResourceBudget
from .resource_control import ResourceLease


@dataclass(frozen=True, slots=True)
class WindowsJobPlan:
    available: bool
    enforceable: bool
    settings: dict[str, int]
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WindowsJobResult:
    applied: bool
    verified: bool
    pid: int | None
    settings: dict[str, int]
    reasons: tuple[str, ...] = ()


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong), ("LimitFlags", ctypes.c_uint32), ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", ctypes.c_uint32), ("Affinity", ctypes.c_size_t), ("PriorityClass", ctypes.c_uint32), ("SchedulingClass", ctypes.c_uint32)]


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [("ReadOperationCount", ctypes.c_uint64), ("WriteOperationCount", ctypes.c_uint64), ("OtherOperationCount", ctypes.c_uint64), ("ReadTransferCount", ctypes.c_uint64), ("WriteTransferCount", ctypes.c_uint64), ("OtherTransferCount", ctypes.c_uint64)]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION), ("IoInfo", _IO_COUNTERS), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


class _JOBOBJECT_CPU_RATE_CONTROL_INFORMATION(ctypes.Structure):
    _fields_ = [("ControlFlags", ctypes.c_uint32), ("CpuRate", ctypes.c_uint32)]


class WindowsJobObjectBackend:
    name = "windows-job-object"
    JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
    JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
    JOB_OBJECT_CPU_RATE_CONTROL_ENABLE = 0x1
    JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP = 0x4
    JobObjectExtendedLimitInformation = 9
    JobObjectCpuRateControlInformation = 15

    def __init__(self) -> None:
        self._kernel32: Any | None = None
        self._jobs: dict[int, Any] = {}
        if os.name == "nt":
            self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            self._configure_api()

    def _configure_api(self) -> None:
        assert self._kernel32 is not None
        k = self._kernel32
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        k.CreateJobObjectW.restype = ctypes.c_void_p
        k.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        k.SetInformationJobObject.restype = ctypes.c_int
        k.QueryInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        k.QueryInformationJobObject.restype = ctypes.c_int
        k.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        k.AssignProcessToJobObject.restype = ctypes.c_int
        k.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        k.OpenProcess.restype = ctypes.c_void_p
        k.CloseHandle.argtypes = [ctypes.c_void_p]
        k.CloseHandle.restype = ctypes.c_int

    def plan(self, lease: ResourceLease | None, budget: ResourceBudget) -> WindowsJobPlan:
        settings = {key: value for key, value in {"memory_bytes": budget.memory_bytes, "cpu_millis": budget.cpu_millis, "pids": budget.pids, "disk_bytes": budget.disk_bytes}.items() if value is not None}
        if not settings:
            return WindowsJobPlan(os.name == "nt", True, {})
        if os.name != "nt":
            return WindowsJobPlan(False, False, {}, ("windows_required",))
        if lease is None:
            return WindowsJobPlan(True, False, {}, ("resource_lease_required",))
        errors = lease.validate()
        if errors:
            return WindowsJobPlan(True, False, {}, errors)
        if not lease.active:
            return WindowsJobPlan(True, False, {}, ("resource_lease_inactive",))
        if budget.disk_bytes is not None:
            return WindowsJobPlan(True, False, {}, ("disk_limit_unsupported",))
        if budget.cpu_millis is not None and not 1 <= budget.cpu_millis <= 1000:
            return WindowsJobPlan(True, False, {}, ("cpu_millis_out_of_range",))
        if budget.memory_bytes is not None and budget.memory_bytes <= 0:
            return WindowsJobPlan(True, False, {}, ("memory_bytes_must_be_positive",))
        if budget.pids is not None and budget.pids <= 0:
            return WindowsJobPlan(True, False, {}, ("pids_must_be_positive",))
        return WindowsJobPlan(True, True, settings)

    def _set_limits(self, handle: Any, budget: ResourceBudget) -> tuple[str, ...]:
        assert self._kernel32 is not None
        k = self._kernel32
        info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        if budget.memory_bytes is not None:
            info.BasicLimitInformation.LimitFlags |= self.JOB_OBJECT_LIMIT_JOB_MEMORY
            info.JobMemoryLimit = budget.memory_bytes
        if budget.pids is not None:
            info.BasicLimitInformation.LimitFlags |= self.JOB_OBJECT_LIMIT_ACTIVE_PROCESS
            info.BasicLimitInformation.ActiveProcessLimit = budget.pids
        if info.BasicLimitInformation.LimitFlags and not k.SetInformationJobObject(handle, self.JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)):
            return (f"set_extended_limits_failed:{ctypes.get_last_error()}",)
        if budget.cpu_millis is not None:
            cpu = _JOBOBJECT_CPU_RATE_CONTROL_INFORMATION(self.JOB_OBJECT_CPU_RATE_CONTROL_ENABLE | self.JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP, budget.cpu_millis * 100)
            if not k.SetInformationJobObject(handle, self.JobObjectCpuRateControlInformation, ctypes.byref(cpu), ctypes.sizeof(cpu)):
                return (f"set_cpu_limit_failed:{ctypes.get_last_error()}",)
        return ()

    def _verify_limits(self, handle: Any, budget: ResourceBudget) -> tuple[str, ...]:
        assert self._kernel32 is not None
        k = self._kernel32
        if budget.memory_bytes is not None or budget.pids is not None:
            info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            size = ctypes.c_uint32()
            if not k.QueryInformationJobObject(handle, self.JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info), ctypes.byref(size)):
                return (f"query_extended_limits_failed:{ctypes.get_last_error()}",)
            if budget.memory_bytes is not None and info.JobMemoryLimit != budget.memory_bytes:
                return ("memory_limit_verification_failed",)
            if budget.pids is not None and info.BasicLimitInformation.ActiveProcessLimit != budget.pids:
                return ("pids_limit_verification_failed",)
        if budget.cpu_millis is not None:
            cpu = _JOBOBJECT_CPU_RATE_CONTROL_INFORMATION()
            size = ctypes.c_uint32()
            if not k.QueryInformationJobObject(handle, self.JobObjectCpuRateControlInformation, ctypes.byref(cpu), ctypes.sizeof(cpu), ctypes.byref(size)):
                return (f"query_cpu_limit_failed:{ctypes.get_last_error()}",)
            expected_flags = self.JOB_OBJECT_CPU_RATE_CONTROL_ENABLE | self.JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP
            if cpu.ControlFlags != expected_flags or cpu.CpuRate != budget.cpu_millis * 100:
                return ("cpu_limit_verification_failed",)
        return ()

    def apply(self, pid: int, lease: ResourceLease, budget: ResourceBudget) -> WindowsJobResult:
        plan = self.plan(lease, budget)
        if not plan.enforceable:
            return WindowsJobResult(False, False, pid, {}, plan.reasons)
        if self._kernel32 is None:
            return WindowsJobResult(False, False, pid, {}, ("windows_required",))
        handle = self._kernel32.CreateJobObjectW(None, None)
        if not handle:
            return WindowsJobResult(False, False, pid, {}, (f"create_job_failed:{ctypes.get_last_error()}",))
        reasons = self._set_limits(handle, budget)
        if reasons:
            self._kernel32.CloseHandle(handle)
            return WindowsJobResult(False, False, pid, {}, reasons)
        # AssignProcessToJobObject requires a process handle with PROCESS_SET_QUOTA and PROCESS_TERMINATE.
        process_handle = self._kernel32.OpenProcess(0x0100 | 0x0001, False, pid)
        if not process_handle:
            self._kernel32.CloseHandle(handle)
            return WindowsJobResult(False, False, pid, {}, (f"open_process_failed:{ctypes.get_last_error()}",))
        try:
            if not self._kernel32.AssignProcessToJobObject(handle, process_handle):
                reason = (f"assign_process_failed:{ctypes.get_last_error()}",)
                self._kernel32.CloseHandle(handle)
                return WindowsJobResult(False, False, pid, {}, reason)
        finally:
            self._kernel32.CloseHandle(process_handle)
        reasons = self._verify_limits(handle, budget)
        if reasons:
            self._kernel32.CloseHandle(handle)
            return WindowsJobResult(False, False, pid, {}, reasons)
        self._jobs[pid] = handle
        return WindowsJobResult(True, True, pid, plan.settings)

    def release(self, pid: int | None) -> None:
        if pid is None or self._kernel32 is None:
            return
        handle = self._jobs.pop(pid, None)
        if handle:
            self._kernel32.CloseHandle(handle)
