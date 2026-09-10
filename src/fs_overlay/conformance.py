"""Deterministic conformance vectors for the federation protocol surface."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

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
        "f7e3f5c5f4e2c2f8f4b5c4d9f8f2b5d2f8c5f6c6e9b6a6b2a5f5c2d3e8f4a9b1",
    ),
)


def validate_vector(vector: ConformanceVector) -> bool:
    return vector.envelope.digest() == vector.expected_digest


def validate_vectors(vectors: tuple[ConformanceVector, ...] = VECTORS) -> tuple[str, ...]:
    return tuple(vector.name for vector in vectors if validate_vector(vector))
