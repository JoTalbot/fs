from fs_overlay.model import ResourceBudget
from fs_overlay.resource_control import ResourceLease, plan_resources


def test_empty_budget_needs_no_lease():
    plan = plan_resources(ResourceBudget())
    assert plan.enforceable
    assert plan.reasons == ()


def test_requested_budget_requires_lease():
    plan = plan_resources(ResourceBudget(memory_bytes=1024))
    assert not plan.enforceable
    assert "resource_lease_required" in plan.reasons


def test_invalid_lease_fails_closed():
    lease = ResourceLease(lease_id="", scope="", owner="")
    plan = plan_resources(ResourceBudget(cpu_millis=1000), lease)
    assert not plan.enforceable
    assert "lease_id is required" in plan.reasons


def test_valid_lease_still_requires_native_controller():
    lease = ResourceLease("lease-1", "fs/workloads/demo", "node-1")
    plan = plan_resources(ResourceBudget(memory_bytes=1024), lease)
    assert plan.lease_id == "lease-1"
    assert not plan.enforceable
    assert "native_resource_controller_not_attached" in plan.reasons
