"""Semantic ABI compatibility adapter.

This layer bridges versioned backend contracts with negotiated semantic
capabilities. It performs compatibility checks only; it never grants
execution authority or mutates backend state.
"""
from __future__ import annotations

from dataclasses import dataclass

from .backend_contract import BackendContract
from .capability_negotiation import CapabilitySet


@dataclass(frozen=True, slots=True)
class SemanticABIAdapter:
    contract: BackendContract
    capabilities: CapabilitySet

    def supports(self, *, contract_version: int, required_features: frozenset[str] = frozenset()) -> bool:
        if not self.contract.compatible_with(contract_version):
            return False
        if not required_features.issubset(self.capabilities.features):
            return False
        return True

    def canonical(self) -> dict[str, object]:
        return {
            "backend_id": self.contract.backend_id,
            "contract_version": self.contract.version,
            "protocol_version": self.capabilities.protocol_version,
            "features": sorted(self.capabilities.features),
        }
