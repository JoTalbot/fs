"""Minimal backend-neutral semantic execution core.

This module deliberately does not touch the host. It provides deterministic
contracts used by planners, simulators and future platform adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class Idempotency(StrEnum):
    IDEMPOTENT = "idempotent"
    NON_IDEMPOTENT = "non_idempotent"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Operation:
    operation_id: str
    target: str
    requires: frozenset[str] = frozenset()
    authority_scope: str = ""
    preconditions: tuple[str, ...] = ()
    effects: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    idempotency: Idempotency = Idempotency.UNKNOWN
    inputs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PlanNode:
    node_id: str
    operation: Operation
    depends_on: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class PlanDAG:
    nodes: tuple[PlanNode, ...]

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        ids = [node.node_id for node in self.nodes]
        if len(ids) != len(set(ids)):
            errors.append("duplicate plan node id")
        known = set(ids)
        for node in self.nodes:
            missing = node.depends_on - known
            if missing:
                errors.append(f"{node.node_id}: missing dependencies {sorted(missing)}")
            if not node.operation.operation_id:
                errors.append(f"{node.node_id}: missing operation id")
            if not node.operation.preconditions:
                errors.append(f"{node.node_id}: missing preconditions")
            if not node.operation.postconditions:
                errors.append(f"{node.node_id}: missing postconditions")
            if node.operation.idempotency is Idempotency.UNKNOWN:
                errors.append(f"{node.node_id}: idempotency is unknown")
        if not errors and self._has_cycle():
            errors.append("plan contains dependency cycle")
        return tuple(errors)

    def _has_cycle(self) -> bool:
        graph = {n.node_id: set(n.depends_on) for n in self.nodes}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> bool:
            if node_id in visiting:
                return True
            if node_id in visited:
                return False
            visiting.add(node_id)
            if any(visit(dep) for dep in graph[node_id]):
                return True
            visiting.remove(node_id)
            visited.add(node_id)
            return False

        return any(visit(node_id) for node_id in graph)


@dataclass(frozen=True, slots=True)
class StateTransition:
    transition_id: str
    object_id: str
    from_state: str
    trigger: str
    preconditions: tuple[str, ...]
    effects: tuple[str, ...]
    postconditions: tuple[str, ...]
    to_state: str

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.object_id:
            errors.append("missing object id")
        if not self.from_state or not self.to_state:
            errors.append("missing state")
        if not self.preconditions:
            errors.append("missing preconditions")
        if not self.effects:
            errors.append("missing effects")
        if not self.postconditions:
            errors.append("missing postconditions")
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    execution_id: str
    operation_id: str
    backend: str
    status: str
    evidence: tuple[str, ...] = ()
    verified: bool = False

    def can_commit(self) -> bool:
        return self.status == "succeeded" and self.verified


class Backend(Protocol):
    """Backend contract. Implementations must not exceed the admitted scope."""

    name: str

    def execute(self, operation: Operation) -> ExecutionRecord:
        ...


class ReferenceSimulationBackend:
    """Deterministic backend for tests and what-if execution.

    It records execution semantics but performs no host-side mutation.
    """

    name = "simulation"

    def execute(self, operation: Operation) -> ExecutionRecord:
        if not operation.preconditions or not operation.postconditions:
            return ExecutionRecord(
                execution_id=f"sim:{operation.operation_id}",
                operation_id=operation.operation_id,
                backend=self.name,
                status="rejected",
                evidence=("missing verification contract",),
            )
        return ExecutionRecord(
            execution_id=f"sim:{operation.operation_id}",
            operation_id=operation.operation_id,
            backend=self.name,
            status="succeeded",
            evidence=("simulation-only", "no-host-mutation"),
            verified=True,
        )
