"""Dependency-free semantic state primitives used by the FS control plane.

These are contracts and deterministic data structures, not authority by themselves.
Execution remains subject to policy, admission, verification and backend evidence.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Iterable, Mapping


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _identity(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


@dataclass(frozen=True)
class ObjectContract:
    object_type: str
    object_id: str
    generation: int
    desired: Mapping[str, object]
    actual: Mapping[str, object]
    health: str
    location: str | None = None

    def identity(self) -> str:
        return _identity({"object_type": self.object_type, "object_id": self.object_id,
                          "generation": self.generation, "desired": self.desired,
                          "actual": self.actual, "health": self.health, "location": self.location})

    def transition(self, *, actual: Mapping[str, object], health: str,
                   generation: int | None = None) -> "ObjectContract":
        next_generation = self.generation + 1 if generation is None else generation
        if next_generation <= self.generation:
            raise ValueError("object generation must increase")
        return ObjectContract(self.object_type, self.object_id, next_generation,
                              self.desired, dict(actual), health, self.location)


@dataclass(frozen=True)
class ProvenanceRecord:
    subject_id: str
    source: str
    operation: str
    actor: str
    timestamp_ns: int
    parent_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    record_id: str = ""

    def identity(self) -> str:
        return _identity({"subject_id": self.subject_id, "source": self.source,
                          "operation": self.operation, "actor": self.actor,
                          "timestamp_ns": self.timestamp_ns, "parent_ids": self.parent_ids,
                          "evidence_ids": self.evidence_ids})

    def materialize(self) -> "ProvenanceRecord":
        return ProvenanceRecord(self.subject_id, self.source, self.operation, self.actor,
                                self.timestamp_ns, self.parent_ids, self.evidence_ids, self.identity())


@dataclass(frozen=True)
class Dependency:
    subject_id: str
    depends_on: str
    relation: str = "requires"


class DependencyGraph:
    def __init__(self, dependencies: Iterable[Dependency] = ()):
        self._edges: set[Dependency] = set(dependencies)

    def add(self, dependency: Dependency) -> None:
        if dependency.subject_id == dependency.depends_on:
            raise ValueError("self dependency is not allowed")
        candidate = set(self._edges)
        candidate.add(dependency)
        self._validate(candidate)
        self._edges = candidate

    @staticmethod
    def _validate(edges: set[Dependency]) -> None:
        graph: dict[str, set[str]] = {}
        for edge in edges:
            graph.setdefault(edge.subject_id, set()).add(edge.depends_on)
            graph.setdefault(edge.depends_on, set())
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError("dependency cycle detected")
            if node in visited:
                return
            visiting.add(node)
            for parent in sorted(graph[node]):
                visit(parent)
            visiting.remove(node)
            visited.add(node)
        for node in sorted(graph):
            visit(node)

    def edges(self) -> tuple[Dependency, ...]:
        return tuple(sorted(self._edges, key=lambda edge: (edge.subject_id, edge.depends_on, edge.relation)))

    def prerequisites(self, subject_id: str) -> tuple[str, ...]:
        return tuple(sorted(edge.depends_on for edge in self._edges if edge.subject_id == subject_id))


@dataclass(frozen=True)
class Lease:
    lease_id: str
    resource_id: str
    owner_id: str
    issued_ns: int
    expires_ns: int
    fence: int
    revoked: bool = False

    @classmethod
    def issue(cls, resource_id: str, owner_id: str, *, duration_ns: int, fence: int) -> "Lease":
        if duration_ns <= 0 or fence < 0:
            raise ValueError("invalid lease parameters")
        now = time.time_ns()
        return cls(uuid.uuid4().hex, resource_id, owner_id, now, now + duration_ns, fence)

    def valid(self, *, now_ns: int | None = None, expected_fence: int | None = None) -> bool:
        now = time.time_ns() if now_ns is None else now_ns
        return not self.revoked and self.issued_ns <= now < self.expires_ns and (expected_fence is None or self.fence == expected_fence)

    def revoke(self) -> "Lease":
        return Lease(self.lease_id, self.resource_id, self.owner_id, self.issued_ns,
                     self.expires_ns, self.fence, True)


@dataclass(frozen=True)
class KnowledgeRecord:
    subject_id: str
    claim: str
    confidence: float
    source_ids: tuple[str, ...]
    observed_ns: int
    record_id: str = ""

    def materialize(self) -> "KnowledgeRecord":
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        identity = _identity({"subject_id": self.subject_id, "claim": self.claim,
                              "confidence": self.confidence, "source_ids": self.source_ids,
                              "observed_ns": self.observed_ns})
        return KnowledgeRecord(self.subject_id, self.claim, self.confidence,
                               self.source_ids, self.observed_ns, identity)


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    subject_id: str
    recommendation: str
    rationale: str
    evidence_ids: tuple[str, ...]
    policy_ids: tuple[str, ...]
    confidence: float
    created_ns: int

    @classmethod
    def create(cls, subject_id: str, recommendation: str, rationale: str,
               *, evidence_ids: Iterable[str] = (), policy_ids: Iterable[str] = (),
               confidence: float = 0.0) -> "DecisionRecord":
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        evidence = tuple(evidence_ids)
        policies = tuple(policy_ids)
        identity = _identity({"subject_id": subject_id, "recommendation": recommendation,
                              "rationale": rationale, "evidence_ids": evidence,
                              "policy_ids": policies, "confidence": confidence})
        return cls(identity, subject_id, recommendation, rationale, evidence, policies,
                   confidence, time.time_ns())


@dataclass(frozen=True)
class WorldStateSnapshot:
    snapshot_id: str
    generation: int
    objects: tuple[str, ...]
    observations: tuple[str, ...]
    created_ns: int

    @classmethod
    def create(cls, objects: Iterable[str], observations: Iterable[str], *, generation: int) -> "WorldStateSnapshot":
        object_ids = tuple(sorted(set(objects)))
        observation_ids = tuple(sorted(set(observations)))
        identity = _identity({"generation": generation, "objects": object_ids,
                              "observations": observation_ids})
        return cls(identity, generation, object_ids, observation_ids, time.time_ns())


@dataclass(frozen=True)
class ControlLoopResult:
    subject_id: str
    observed_state: Mapping[str, object]
    desired_state: Mapping[str, object]
    decision_id: str | None
    action: str | None
    verified: bool
    safe_stop: bool
    reason: str | None = None


def reconcile(desired: Mapping[str, object], actual: Mapping[str, object]) -> tuple[str, ...]:
    """Return deterministic changed keys; this function performs no mutation."""
    return tuple(sorted(key for key in set(desired) | set(actual) if desired.get(key) != actual.get(key)))


def safe_stop(subject_id: str, desired: Mapping[str, object], actual: Mapping[str, object], *, reason: str) -> ControlLoopResult:
    return ControlLoopResult(subject_id, dict(actual), dict(desired), None, None, False, True, reason)
