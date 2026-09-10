import sys

from fs_overlay.adapter import ProcessResult
from fs_overlay.cgroup_v2 import CgroupV2Result
from fs_overlay.model import ResourceBudget
from fs_overlay.supervisor import ProcessSupervisor, SupervisorPolicy
from fs_overlay.resource_control import ResourceLease


class FakeResourceBackend:
    def __init__(self, verified=True):
        self.verified = verified
        self.calls = []

    def apply(self, pid, lease, budget):
        self.calls.append((pid, lease, budget))
        return CgroupV2Result(
            applied=self.verified,
            verified=self.verified,
            pid=pid,
            settings=(),
            reasons=() if self.verified else ("resource_enforcement_failed",),
        )


def python_command(code):
    return (sys.executable, "-c", code)


def test_supervisor_requires_admission():
    result = ProcessSupervisor().execute(python_command("print('ok')"))
    assert result.status == "rejected"


def test_supervisor_runs_without_shell():
    result = ProcessSupervisor().execute(
        python_command("print('ok')"),
        admitted=True,
    )
    assert result.status == "succeeded"
    assert result.stdout.strip() == "ok"
    assert result.backend == "process-supervisor"
    assert "supervised-lifecycle-observed" in result.execution_evidence


def test_supervisor_times_out_and_cleans_up():
    result = ProcessSupervisor().execute(
        python_command("import time; time.sleep(5)"),
        admitted=True,
        policy=SupervisorPolicy(timeout=0.1),
    )
    assert result.status == "timed_out"
    assert result.timed_out


def test_supervisor_restart_policy_retries_failures(monkeypatch):
    calls = []
    supervisor = ProcessSupervisor()

    def fake_once(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            return ProcessResult("failed", 1, "", "failure")
        return ProcessResult("succeeded", 0, "ok", "")

    monkeypatch.setattr(supervisor, "_once", fake_once)
    result = supervisor.execute(
        ("/bin/true",),
        admitted=True,
        policy=SupervisorPolicy(restart="on-failure", max_restarts=1),
    )
    assert result.status == "succeeded"
    assert len(calls) == 2


def test_supervisor_rejects_invalid_restart_policy():
    result = ProcessSupervisor().execute(
        python_command("print('ok')"),
        admitted=True,
        policy=SupervisorPolicy(restart="never", max_restarts=1),
    )
    assert result.status == "rejected"
    assert "max_restarts_requires_on_failure" in result.stderr


def test_supervisor_fails_closed_when_resource_enforcement_fails(tmp_path):
    backend = FakeResourceBackend(verified=False)
    supervisor = ProcessSupervisor(backend)
    lease = ResourceLease("lease-1", str(tmp_path), "fs")
    result = supervisor.execute(
        python_command("print('should-not-commit')"),
        admitted=True,
        resource_lease=lease,
        resource_budget=ResourceBudget(memory_bytes=1024),
    )
    assert result.status == "failed"
    assert "resource_enforcement_failed" in result.stderr
    assert backend.calls
