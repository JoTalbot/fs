from fs_overlay.adapter import ProcessResult
from fs_overlay.execution_coordinator import ExecutionBoundaryPlan
from fs_overlay.resource_control import ResourcePlan
from fs_overlay.transaction_executor import TransactionExecutor
from fs_overlay.workspace import WorkspaceBinding, WorkspacePlan
from fs_overlay.network_namespace import NetworkNamespacePlan
from fs_overlay.model import ResourceBudget


def admitted_plan() -> ExecutionBoundaryPlan:
    return ExecutionBoundaryPlan(
        True,
        WorkspacePlan(WorkspaceBinding("ws", "/tmp", True), True, None),
        NetworkNamespacePlan(True, True),
        ResourcePlan(ResourceBudget(), None, True),
    )


def test_rejected_plan_never_calls_executor():
    called = False

    def executor(**kwargs):
        nonlocal called
        called = True
        return ProcessResult("succeeded", 0, "", "")

    plan = ExecutionBoundaryPlan(
        False,
        WorkspacePlan(WorkspaceBinding("", ""), False, None, ("blocked",)),
        NetworkNamespacePlan(False, False),
        ResourcePlan(ResourceBudget(), None, True),
        ("blocked",),
    )
    result = TransactionExecutor().execute("tx-1", plan, ("true",), executor)
    assert result.state == "rejected"
    assert not called


def test_successful_execution_commits():
    def executor(**kwargs):
        assert kwargs["admitted"] is True
        return ProcessResult("succeeded", 0, "ok", "")

    result = TransactionExecutor().execute("tx-2", admitted_plan(), ("true",), executor)
    assert result.state == "committed"
    assert result.result is not None


def test_failed_execution_does_not_commit():
    def executor(**kwargs):
        return ProcessResult("failed", 1, "", "failure")

    result = TransactionExecutor().execute("tx-3", admitted_plan(), ("false",), executor)
    assert result.state == "failed"
    assert result.result is not None
