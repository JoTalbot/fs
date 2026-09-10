"""Two-node reference federation for safe, deterministic integration tests."""
from __future__ import annotations

from dataclasses import dataclass, field

from .ir import CapabilityRequirement
from .matching import CapabilityOffer, MatchResult, match_capabilities
from .session import ApplicationSession


@dataclass(slots=True)
class SimulatedNode:
    node_id: str
    offers: tuple[CapabilityOffer, ...]
    online: bool = True
    admitted: bool = True
    active_sessions: set[str] = field(default_factory=set)

    def match(self, requirements: tuple[CapabilityRequirement, ...]) -> MatchResult:
        if not self.online or not self.admitted:
            return MatchResult(False, missing=("node unavailable",))
        return match_capabilities(requirements, self.offers)


class SimulatedFederation:
    """Federation model with no sockets, credentials or host mutation."""

    def __init__(self, nodes: tuple[SimulatedNode, ...] = ()) -> None:
        self.nodes = {node.node_id: node for node in nodes}

    def add_node(self, node: SimulatedNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"duplicate node id: {node.node_id}")
        self.nodes[node.node_id] = node

    def place(self, session: ApplicationSession) -> str:
        requirements = tuple(CapabilityRequirement(name=name) for name in session.requirements)
        candidates = [node for node in self.nodes.values() if node.match(requirements).matched]
        if not candidates:
            raise RuntimeError("no admitted node satisfies session requirements")
        node = sorted(candidates, key=lambda item: item.node_id)[0]
        node.active_sessions.add(session.session_id)
        session.bind_execution(node.node_id)
        return node.node_id

    def execute(self, session: ApplicationSession) -> dict[str, str]:
        if session.execution_node is None:
            self.place(session)
        node = self.nodes[session.execution_node]
        if not node.online or not node.admitted:
            session.fail()
            return {"status": "failed", "reason": "execution node unavailable"}
        return {
            "status": "succeeded",
            "session_id": session.session_id,
            "execution_node": node.node_id,
            "presentation": session.presentation_endpoint or "none",
        }
