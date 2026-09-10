"""Explicit post-execution verification contracts.

Verification is evidence, not an assertion derived from process exit status.
Concrete backends may supply checks for namespaces, mounts, resources and
other declared guarantees. Missing evidence fails closed for a requested
check.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping


@dataclass(frozen=True, slots=True)
class VerificationCheck:
    check_id: str
    description: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class VerificationEvidence:
    check_id: str
    passed: bool
    observed: Mapping[str, object]
    reason: str = ""


@dataclass(frozen=True, slots=True)
class VerificationResult:
    verified: bool
    evidence: tuple[VerificationEvidence, ...]
    reasons: tuple[str, ...] = ()


def verify(
    checks: tuple[VerificationCheck, ...],
    evidence_provider: Callable[[VerificationCheck], VerificationEvidence | None],
) -> VerificationResult:
    evidence: list[VerificationEvidence] = []
    reasons: list[str] = []
    for check in checks:
        item = evidence_provider(check)
        if item is None:
            if check.required:
                reasons.append(f"missing_evidence:{check.check_id}")
            continue
        evidence.append(item)
        if check.required and not item.passed:
            reasons.append(item.reason or f"verification_failed:{check.check_id}")
    return VerificationResult(not reasons, tuple(evidence), tuple(reasons))
