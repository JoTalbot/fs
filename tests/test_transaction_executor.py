from fs_overlay.adapter import ProcessResult
from fs_overlay.execution_coordinator import ExecutionBoundaryPlan
from fs_overlay.mount_namespace import MountNamespacePlan
from fs_overlay.network_namespace import NetworkNamespacePlan
from fs_overlay.resource_control import ResourcePlan
from fs_overlay.transaction_executor import TransactionExecutor
from fs_overlay.verification import VerificationEvidence
from fs_overlay.workspace import WorkspaceBinding, WorkspacePlan
from fs_overlay.model import ResourceBudget


def admitted_plan(mount_guarantees=(), network_guarantees=()) -> ExecutionBoundaryPlan:
    return ExecutionBoundaryPlan(
        True,
        WorkspacePlan(WorkspaceBinding("ws", "/tmp", True), True, None),
        MountNamespacePlan(True, True, guarantees=mount_guarantees),
        NetworkNamespacePlan(True, True, guarantees=network_guarantees),
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
        MountNamespacePlan(False, False, reasons=("blocked",)),
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


def test_declared_namespace_guarantee_cannot_be_omitted_from_verification():
    def executor(**kwargs):
        return ProcessResult("succeeded", 0, "ok", "")

    result = TransactionExecutor().execute(
        "tx-4",
        admitted_plan(("mount-namespace",)),
        ("true",),
        executor,
        evidence_provider=lambda check: None,
    )
    assert result.state == "verification_failed"
    assert result.verification is not None
    assert "missing_evidence:namespace:mount" in result.verification.reasons


def test_declared_namespace_guarantee_commits_with_matching_evidence():
    def executor(**kwargs):
        return ProcessResult("succeeded", 0, "ok", "")

    def evidence_provider(check):
        return VerificationEvidence(check.check_id, True, {"probe": "test"})

    result = TransactionExecutor().execute(
        "tx-5",
        admitted_plan(("mount-namespace",), ("network-namespace",)),
        ("true",),
        executor,
        evidence_provider=evidence_provider,
    )
    assert result.state == "committed"
    assert result.verification is not None
    assert [item.check_id for item in result.verification.evidence] == [
        "namespace:mount",
        "namespace:net",
    ]
