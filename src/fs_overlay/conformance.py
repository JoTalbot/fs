"""Deterministic conformance vectors for the federation protocol surface."""
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


def validate_vectors(vectors: tuple[ConformanceVector, ...] = VECTORS) -> tuple[str, ...]:
    return tuple(vector.name for vector in vectors if validate_vector(vector))
