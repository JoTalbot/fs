"""Derive required verification checks from declared execution guarantees."""
from __future__ import annotations

from .execution_coordinator import ExecutionBoundaryPlan
from .verification import VerificationCheck


_GUARANTEE_CHECKS = {
    "mount-namespace": VerificationCheck(
        "namespace:mount", "Verify the mount namespace can be created by the runtime probe."
    ),
    "pid-namespace": VerificationCheck(
        "namespace:pid", "Verify the PID namespace can be created by the runtime probe."
    ),
    "network-namespace": VerificationCheck(
        "namespace:net", "Verify the network namespace can be created by the runtime probe."
    ),
    "workspace-filesystem-boundary": VerificationCheck(
        "workspace:boundary", "Verify the exact execution observed the admitted workspace boundary."
    ),
}


def required_verification_checks(plan: ExecutionBoundaryPlan) -> tuple[VerificationCheck, ...]:
    """Return checks required by isolation guarantees declared by an admitted plan.

    This is intentionally conservative. Only guarantees with an explicit
    evidence mapping become required checks. A guarantee without an evidence
    implementation must not silently become a stronger runtime claim.
    """
    guarantees = (*plan.mount.guarantees, *plan.network.guarantees)
    checks: list[VerificationCheck] = []
    seen: set[str] = set()
    for guarantee in guarantees:
        check = _GUARANTEE_CHECKS.get(guarantee)
        if check is not None and check.check_id not in seen:
            checks.append(check)
            seen.add(check.check_id)
    return tuple(checks)
