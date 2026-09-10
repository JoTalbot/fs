from fs_overlay.adapter import ProcessResult
from fs_overlay.linux_executor import LinuxExecutionPolicy
from fs_overlay.model import EnvironmentSpec, ExecutionPolicy, ResourceBudget
from fs_overlay.resource_control import ResourceLease
from fs_overlay.runtime import ExecutionRuntime


class FakeLinuxExecutor:
    def __init__(self):
        self.calls = []

    def execute(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return ProcessResult(
            "succeeded",
            0,
            "ok",
            "",
            backend="process-supervisor",
            execution_evidence=("resource-controller-enforced",),
            resource_lease_id=kwargs["resource_lease"].lease_id,
        )


def test_runtime_commits_only_after_resource_evidence(tmp_path):
    executor = FakeLinuxExecutor()
    runtime = ExecutionRuntime(linux_executor=executor)
    lease = ResourceLease("lease-1", str(tmp_path), "fs")
    spec = EnvironmentSpec(
        name="demo",
        command=("/bin/true",),
        policy=ExecutionPolicy(
            filesystem="host",
            network="host",
            resources=ResourceBudget(memory_bytes=1024),
        ),
    )

    result = runtime.execute("tx-runtime-1", spec, resource_lease=lease)

    assert result.state == "committed"
    assert result.verification is not None
    assert [item.check_id for item in result.verification.evidence] == ["resource:enforcement"]
    assert executor.calls[0][0] == ("/bin/true",)
    assert executor.calls[0][1]["resource_lease"] == lease


def test_runtime_rejects_missing_resource_lease(tmp_path):
    runtime = ExecutionRuntime(linux_executor=FakeLinuxExecutor())
    spec = EnvironmentSpec(
        name="demo",
        command=("/bin/true",),
        policy=ExecutionPolicy(
            filesystem="host",
            network="host",
            resources=ResourceBudget(memory_bytes=1024),
        ),
    )

    result = runtime.execute("tx-runtime-2", spec)

    assert result.state == "rejected"
    assert "resource_lease_required" in result.reasons
