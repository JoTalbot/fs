"""Explicit admission and resource-sharing primitives for the FS fabric."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ShareClass(StrEnum):
    PRIVATE = "private"
    SHARED = "shared"
    LEASED = "leased"
    FEDERATED = "federated"
    PUBLIC = "public"


@dataclass(frozen=True, slots=True)
class Node:
    node_id: str
    platform: str
    capabilities: frozenset[str]
    share_classes: frozenset[ShareClass] = frozenset({ShareClass.PRIVATE})
    trusted: bool = False


@dataclass(frozen=True, slots=True)
class ResourceOffer:
    offer_id: str
    node_id: str
    capability: str
    quantity: float
    unit: str
    share_class: ShareClass
    lease_seconds: int | None = None
    private_data_included: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.offer_id or not self.node_id or not self.capability:
            errors.append("missing resource identity")
        if self.quantity < 0:
            errors.append("negative resource quantity")
        if self.share_class is ShareClass.PRIVATE:
            errors.append("private resource cannot be offered to the fabric")
        if self.lease_seconds is not None and self.lease_seconds <= 0:
            errors.append("lease must be positive")
        if self.private_data_included:
            errors.append("private data cannot be implicitly shared")
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class ResourceRequest:
    request_id: str
    principal_id: str
    capability: str
    quantity: float
    unit: str
    allowed_node_ids: frozenset[str] = frozenset()
    require_trusted: bool = True


@dataclass(frozen=True, slots=True)
class Allocation:
    allocation_id: str
    request_id: str
    offer_id: str
    quantity: float
    lease_seconds: int


class ResourceFabric:
    """Small deterministic matcher; trust/admission remain explicit inputs."""

    def match(self, request: ResourceRequest, offers: tuple[ResourceOffer, ...], nodes: tuple[Node, ...]) -> tuple[ResourceOffer, ...]:
        node_map = {node.node_id: node for node in nodes}
        matches: list[ResourceOffer] = []
        for offer in offers:
            node = node_map.get(offer.node_id)
            if node is None or offer.validate():
                continue
            if offer.capability != request.capability or offer.quantity < request.quantity:
                continue
            if request.allowed_node_ids and offer.node_id not in request.allowed_node_ids:
                continue
            if request.require_trusted and not node.trusted:
                continue
            matches.append(offer)
        return tuple(sorted(matches, key=lambda item: (item.quantity, item.node_id, item.offer_id)))
