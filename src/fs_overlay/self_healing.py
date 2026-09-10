"""Deterministic self-healing plans from verified replica observations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .replication import ReplicaAction


@dataclass(frozen=True)
class ReplicaObservation:
    node_id: str
    object_id: str
    present: bool
    sha256: str | None
    healthy: bool = True


class SelfHealingPlanner:
    """Create repair actions only from explicit observations and policy."""

    def plan(self, object_id: str, observations: Iterable[ReplicaObservation],
             *, desired_copies: int = 2, trusted_nodes: Iterable[str] = ()) -> tuple[ReplicaAction, ...]:
        if desired_copies <= 0:
            raise ValueError("desired_copies must be positive")
        trusted = set(trusted_nodes)
        relevant = [item for item in observations if item.object_id == object_id and item.node_id in trusted]
        valid = [item for item in relevant if item.present and item.healthy and item.sha256]
        if not valid or len(valid) >= desired_copies:
            return ()
        targets = sorted(item.node_id for item in relevant if not item.present and item.healthy)
        source = sorted(valid, key=lambda item: item.node_id)[0]
        needed = desired_copies - len(valid)
        return tuple(
            ReplicaAction(object_id, source.node_id, target, source.sha256)
            for target in targets[:needed]
            if target != source.node_id
        )
