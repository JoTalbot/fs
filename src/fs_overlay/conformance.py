"""Deterministic, versioned conformance vectors for federation semantics."""
from __future__ import annotations

from dataclasses import dataclass

from .federation_protocol import FederationEnvelope


@dataclass(frozen=True)
class ConformanceVector:
    name: str
    envelope: FederationEnvelope
    expected_digest: str


# Versioned vectors are intentionally tiny and independent of crypto libraries.
VECTORS = (
    ConformanceVector(
        "observe-v1",
        FederationEnvelope("node-a", "msg-1", "OBSERVE", 1, 1_000_000_000, {"object": "x"}),
        "28658d631d54184b12983de242bc1ab37f5d2002756b382f995b3a0606799404",
    ),
)


def validate_vector(vector: ConformanceVector) -> bool:
    return vector.envelope.digest() == vector.expected_digest


def validate_vectors(
    vectors: tuple[ConformanceVector, ...] = VECTORS,
    *,
    strict: bool = False,
) -> tuple[str, ...]:
    """Return passing vector names, optionally failing on any mismatch.

    The non-strict form preserves the historical API. Independent harnesses
    should use ``strict=True`` so a missing or mismatched vector cannot be
    mistaken for successful conformance.
    """
    passed = tuple(vector.name for vector in vectors if validate_vector(vector))
    if strict and len(passed) != len(vectors):
        failed = tuple(vector.name for vector in vectors if not validate_vector(vector))
        raise AssertionError(f"conformance vector mismatch: {failed}")
    return passed
