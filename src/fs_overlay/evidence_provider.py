"""Default evidence dispatch for execution-boundary verification."""
from __future__ import annotations

from .probe_verification import linux_namespace_evidence
from .verification import VerificationCheck, VerificationEvidence


def default_evidence_provider(
    check: VerificationCheck,
    *,
    execution_result: object | None = None,
) -> VerificationEvidence | None:
    """Return execution-scoped or reference evidence without inventing proof.

    Concrete Bubblewrap and supervisor evidence is accepted only from the
    exact execution result. Other namespace checks continue to use disposable
    Linux capability probes.
    """
    backend = getattr(execution_result, "backend", None)
    evidence = getattr(execution_result, "execution_evidence", ())
    if check.check_id == "workspace:boundary":
        passed = backend == "bubblewrap-workspace" and "workspace-filesystem-boundary-observed" in evidence
        return VerificationEvidence(
            check.check_id,
            passed,
            {
                "backend": backend,
                "execution_evidence": tuple(evidence),
            },
            "workspace_boundary_not_observed" if not passed else "workspace_boundary_observed",
        )
    if check.check_id == "namespace:net" and backend == "bubblewrap-workspace":
        passed = "network-namespace-observed" in evidence
        return VerificationEvidence(
            check.check_id,
            passed,
            {
                "backend": backend,
                "execution_evidence": tuple(evidence),
            },
            "network_namespace_not_observed" if not passed else "network_namespace_observed",
        )
    if check.check_id == "resource:enforcement":
        passed = (
            backend == "process-supervisor"
            and "resource-controller-enforced" in evidence
        )
        return VerificationEvidence(
            check.check_id,
            passed,
            {
                "backend": backend,
                "execution_evidence": tuple(evidence),
            },
            "resource_enforcement_not_observed" if not passed else "resource_enforcement_observed",
        )
    return linux_namespace_evidence(check)
