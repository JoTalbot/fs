"""Default evidence dispatch for execution-boundary verification."""
from __future__ import annotations

from .probe_verification import linux_namespace_evidence
from .verification import VerificationCheck, VerificationEvidence


def default_evidence_provider(
    check: VerificationCheck,
    *,
    execution_result: object | None = None,
) -> VerificationEvidence | None:
    """Return evidence for checks supported by the reference runtime.

    Workspace evidence is accepted only from the concrete Bubblewrap executor's
    execution result. The generic disposable workspace probe is deliberately
    not used here because it proves a different process.
    """
    if check.check_id == "workspace:boundary":
        backend = getattr(execution_result, "backend", None)
        evidence = getattr(execution_result, "execution_evidence", ())
        passed = backend == "bubblewrap-workspace" and "workspace:boundary-observed" in evidence
        return VerificationEvidence(
            check.check_id,
            passed,
            {
                "backend": backend,
                "execution_evidence": tuple(evidence),
            },
            "workspace_boundary_not_observed" if not passed else "workspace_boundary_observed",
        )
    return linux_namespace_evidence(check)
