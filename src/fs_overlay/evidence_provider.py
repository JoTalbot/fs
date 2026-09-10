"""Default evidence dispatch for execution-boundary verification."""
from __future__ import annotations

from .probe_verification import linux_namespace_evidence
from .verification import VerificationCheck, VerificationEvidence


def default_evidence_provider(check: VerificationCheck) -> VerificationEvidence | None:
    """Return evidence for checks supported by the reference runtime.

    Unknown checks deliberately return ``None`` so the verification layer
    fails closed instead of inventing evidence.
    """
    return linux_namespace_evidence(check)
