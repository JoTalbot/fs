"""Plan-only resource admission contracts for FS execution.

This module deliberately does not write to the host cgroup hierarchy. A
resource limit becomes enforceable only after an explicit lease identifies an
FS-owned/delegated scope. This keeps resource governance separate from mere
filesystem access and avoids assuming host-wide administrative control.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import ResourceBudget


@dataclass(frozen=True, slots=True)
class ResourceLease:
    """Explicit authority to use a bounded resource scope."""

    lease_id: str
    scope: str
    owner: str
    active: bool = True

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.lease_id:
            errors.append("lease_id is required")
        if not self.scope:
            errors.append("scope is required")
        if not self.owner:
            errors.append("owner is required")
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class ResourcePlan:
    budget: ResourceBudget
    lease_id: str | None
    enforceable: bool
    reasons: tuple[str, ...] = ()


def plan_resources(budget: ResourceBudget, lease: ResourceLease | None = None) -> ResourcePlan:
    """Describe resource enforcement without mutating host state.

    A non-empty budget without an active, valid lease is intentionally not
    enforceable. This is the boundary future cgroup/Job Object adapters must
    satisfy before claiming hard limits.
    """
    requested = any(
        value is not None
        for value in (budget.cpu_millis, budget.memory_bytes, budget.disk_bytes, budget.pids)
    )
    if not requested:
        return ResourcePlan(budget, lease.lease_id if lease else None, True)

    if lease is None:
        return ResourcePlan(budget, None, False, ("resource_lease_required",))
    errors = lease.validate()
    if errors:
        return ResourcePlan(budget, lease.lease_id, False, errors)
    if not lease.active:
        return ResourcePlan(budget, lease.lease_id, False, ("resource_lease_inactive",))

    return ResourcePlan(
        budget,
        lease.lease_id,
        False,
        ("native_resource_controller_not_attached",),
    )
