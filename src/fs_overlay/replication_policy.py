"""Deterministic replica placement policy with explicit failure-domain diversity."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ReplicaCandidate:
    node_id: str
    failure_domain: str
    healthy: bool = True
    capacity_available: int = 0
    locality: int = 0


class ReplicaPolicy:
    """Choose deterministic targets while maximizing failure-domain diversity."""

    def plan(self, candidates: Iterable[ReplicaCandidate], *, present_on: Iterable[str], desired_copies: int = 2) -> tuple[str, ...]:
        if desired_copies <= 0:
            raise ValueError("desired_copies must be positive")
        present = set(present_on)
        existing_domains = {c.failure_domain for c in candidates if c.node_id in present}
        eligible = [c for c in candidates if c.healthy and c.capacity_available >= 0 and c.node_id not in present]
        needed = max(0, desired_copies - len(present))
        selected: list[ReplicaCandidate] = []
        used_domains = set(existing_domains)
        for candidate in sorted(eligible, key=lambda c: (-int(c.failure_domain not in used_domains), -c.capacity_available, -c.locality, c.node_id)):
            if len(selected) >= needed:
                break
            if candidate.failure_domain in used_domains and any(x.failure_domain not in used_domains for x in eligible[len(selected):]):
                continue
            selected.append(candidate)
            used_domains.add(candidate.failure_domain)
        if len(selected) < needed:
            for candidate in sorted(eligible, key=lambda c: (-c.capacity_available, -c.locality, c.node_id)):
                if len(selected) >= needed or candidate in selected:
                    continue
                selected.append(candidate)
        return tuple(c.node_id for c in selected)
