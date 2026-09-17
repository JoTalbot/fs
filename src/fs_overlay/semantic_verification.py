"""Semantic verification adapter built on the explicit evidence contract."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .verification import VerificationCheck, VerificationEvidence, VerificationResult, verify


@dataclass(frozen=True, slots=True)
class SemanticVerificationAdapter:
    """Require explicit evidence for semantic guarantees."""

    def verify_required(
        self,
        checks: tuple[VerificationCheck, ...],
        evidence_provider: Callable[[VerificationCheck], VerificationEvidence | None],
    ) -> VerificationResult:
        return verify(checks, evidence_provider)
