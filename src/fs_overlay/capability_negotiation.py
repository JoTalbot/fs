"""Deterministic capability negotiation independent of transport."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilitySet:
    protocol_version: int
    features: frozenset[str]

    def canonical(self) -> tuple[int, tuple[str, ...]]:
        return self.protocol_version, tuple(sorted(self.features))


@dataclass(frozen=True)
class NegotiatedCapabilities:
    protocol_version: int
    features: tuple[str, ...]


def negotiate(local: CapabilitySet, remote: CapabilitySet) -> NegotiatedCapabilities | None:
    if local.protocol_version != remote.protocol_version:
        return None
    return NegotiatedCapabilities(local.protocol_version, tuple(sorted(local.features & remote.features)))
