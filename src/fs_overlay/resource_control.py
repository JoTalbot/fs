"""Resource admission contracts for FS execution.

This module does not mutate host resource-control state. A resource limit is
admitted only when an explicit lease exists. Concrete backends independently
verify that the leased scope can actually enforce the requested budget.
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
    guarantees: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


def plan_resources(budget: ResourceBudget, lease: ResourceLease | None = None) -> ResourcePlan:
    """Describe resource admission without mutating host state.

    A non-empty budget requires an active, valid lease. The concrete runtime
    backend is responsible for proving that the lease scope can enforce the
    requested controller values. A resource guarantee is therefore a required
    post-execution verification, not proof supplied by admission itself.
    """
    requested = any(
        value is not None
        for value in (budget.cpu_millis, budget.memory_bytes, budget.disk_bytes, budget.pids)
    )
    if not requested:
        return ResourcePlan(budget, lease.lease_id if lease else None, True)

    if lease is None:
        return ResourcePlan(budget, None, False, reasons=("resource_lease_required",))
    errors = lease.validate()
    if errors:
        return ResourcePlan(budget, lease.lease_id, False, reasons=errors)
    if not lease.active:
        return ResourcePlan(budget, lease.lease_id, False, reasons=("resource_lease_inactive",))

    # Admission is intentionally separate from backend enforcement.
    return ResourcePlan(
        budget,
        lease.lease_id,
        True,
        guarantees=("resource-controller",),
    )
