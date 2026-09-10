"""Adapters that turn runtime namespace probes into verification evidence."""
from __future__ import annotations

from .linux_probe import probe_namespace
from .verification import VerificationCheck, VerificationEvidence


def linux_namespace_evidence(check: VerificationCheck) -> VerificationEvidence | None:
    """Produce evidence only for checks using the explicit ``namespace:*`` form."""
    prefix, _, namespace = check.check_id.partition(":")
    if prefix != "namespace" or namespace not in {"mount", "pid", "net"}:
        return None
    result = probe_namespace(namespace)
    return VerificationEvidence(
        check_id=check.check_id,
        passed=result.supported,
        observed={
            "namespace": result.namespace,
            "returncode": result.returncode,
            "detail": result.detail,
        },
        reason="" if result.supported else f"namespace_probe_failed:{namespace}",
    )
