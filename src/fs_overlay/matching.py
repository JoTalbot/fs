"""Deterministic capability matching for the FS Resource Fabric."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .ir import CapabilityRequirement


@dataclass(frozen=True, slots=True)
class CapabilityOffer:
    name: str
    capacity: int | float | None = None
    unit: str = ""
    attributes: Mapping[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.attributes is None:
            object.__setattr__(self, "attributes", {})


@dataclass(frozen=True, slots=True)
class MatchResult:
    matched: bool
    missing: tuple[str, ...] = ()
    insufficient: tuple[str, ...] = ()
    incompatible: tuple[str, ...] = ()


def match_capabilities(
    requirements: tuple[CapabilityRequirement, ...],
    offers: tuple[CapabilityOffer, ...],
) -> MatchResult:
    """Match every required capability without granting authority.

    An optional requirement is reported only when an offer exists but is
    incompatible or insufficient. This keeps scheduling deterministic.
    """
    by_name = {offer.name: offer for offer in offers}
    missing: list[str] = []
    insufficient: list[str] = []
    incompatible: list[str] = []

    for req in requirements:
        offer = by_name.get(req.name)
        if offer is None:
            if not req.optional:
                missing.append(req.name)
            continue
        if req.unit and offer.unit and req.unit != offer.unit:
            incompatible.append(req.name)
            continue
        if req.minimum is not None:
            if offer.capacity is None or offer.capacity < req.minimum:
                insufficient.append(req.name)

    return MatchResult(
        matched=not missing and not insufficient and not incompatible,
        missing=tuple(sorted(missing)),
        insufficient=tuple(sorted(insufficient)),
        incompatible=tuple(sorted(incompatible)),
    )
