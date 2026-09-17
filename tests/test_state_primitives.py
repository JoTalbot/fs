"""Qualification of the semantic state primitives used by the FS control plane.

These primitives are contracts, not authority. The tests below pin the
deterministic identity, generation and fail-closed behaviour the roadmap claims
for them.
"""
from __future__ import annotations

import pytest

from fs_overlay.state_primitives import (
    ControlLoopResult,
    DecisionRecord,
    Dependency,
    DependencyGraph,
    KnowledgeRecord,
    Lease,
    ObjectContract,
    ProvenanceRecord,
    WorldStateSnapshot,
    reconcile,
    safe_stop,
)


def _contract(generation: int = 1) -> ObjectContract:
    return ObjectContract(
        object_type="workload",
        object_id="object-a",
        generation=generation,
        desired={"state": "running"},
        actual={"state": "stopped"},
        health="degraded",
        location="node-a",
    )


def test_object_contract_identity_is_content_bound() -> None:
    first = _contract()
    second = _contract()

    assert first.identity() == second.identity()
    assert first.identity() != _contract(generation=2).identity()


def test_object_contract_transition_advances_generation() -> None:
    updated = _contract().transition(actual={"state": "running"}, health="healthy")

    assert updated.generation == 2
    assert updated.actual == {"state": "running"}
    assert updated.health == "healthy"
    assert updated.desired == {"state": "running"}
    assert updated.location == "node-a"


def test_object_contract_transition_rejects_stale_generation() -> None:
    contract = _contract(generation=5)

    with pytest.raises(ValueError):
        contract.transition(actual={}, health="healthy", generation=5)
    with pytest.raises(ValueError):
        contract.transition(actual={}, health="healthy", generation=4)


def test_provenance_record_identity_ignores_record_id_and_binds_lineage() -> None:
    record = ProvenanceRecord("object-a", "storage", "put", "agent-1", 1_000, ("parent-1",), ("evidence-1",))
    materialized = record.materialize()

    assert materialized.record_id == record.identity()
    assert materialized.materialize().record_id == materialized.record_id
    assert materialized.identity() != ProvenanceRecord(
        "object-a", "storage", "put", "agent-1", 1_000, ("parent-2",), ("evidence-1",)
    ).identity()


def test_dependency_graph_reports_deterministic_edges_and_prerequisites() -> None:
    graph = DependencyGraph()
    graph.add(Dependency("build", "checkout"))
    graph.add(Dependency("deploy", "build"))
    graph.add(Dependency("deploy", "approve"))

    assert graph.edges() == tuple(
        sorted(graph.edges(), key=lambda edge: (edge.subject_id, edge.depends_on, edge.relation))
    )
    assert graph.prerequisites("deploy") == ("approve", "build")
    assert graph.prerequisites("unknown") == ()


def test_dependency_graph_rejects_self_dependency() -> None:
    graph = DependencyGraph()

    with pytest.raises(ValueError):
        graph.add(Dependency("build", "build"))
    assert graph.edges() == ()


@pytest.mark.parametrize(
    "edges",
    [
        (Dependency("a", "b"), Dependency("b", "a")),
        (Dependency("a", "b"), Dependency("b", "c"), Dependency("c", "a")),
    ],
)
def test_dependency_graph_rejects_cycles(edges: tuple[Dependency, ...]) -> None:
    graph = DependencyGraph()

    with pytest.raises(ValueError):
        for edge in edges:
            graph.add(edge)


def test_dependency_graph_accepts_diamond_without_false_cycle() -> None:
    graph = DependencyGraph(
        [
            Dependency("d", "b"),
            Dependency("d", "c"),
            Dependency("b", "a"),
            Dependency("c", "a"),
        ]
    )

    assert graph.prerequisites("d") == ("b", "c")
    assert len(graph.edges()) == 4


def test_lease_is_valid_only_inside_its_window_and_fence() -> None:
    lease = Lease("lease-1", "resource-1", "owner-1", issued_ns=100, expires_ns=200, fence=3)

    assert lease.valid(now_ns=100, expected_fence=3) is True
    assert lease.valid(now_ns=199, expected_fence=3) is True
    assert lease.valid(now_ns=99) is False
    assert lease.valid(now_ns=200) is False
    assert lease.valid(now_ns=150, expected_fence=4) is False
    assert lease.revoke().valid(now_ns=150, expected_fence=3) is False


def test_lease_issue_rejects_invalid_parameters() -> None:
    with pytest.raises(ValueError):
        Lease.issue("resource-1", "owner-1", duration_ns=0, fence=0)
    with pytest.raises(ValueError):
        Lease.issue("resource-1", "owner-1", duration_ns=10, fence=-1)


def test_lease_issue_binds_monotonic_window() -> None:
    lease = Lease.issue("resource-1", "owner-1", duration_ns=1_000, fence=1)

    assert lease.expires_ns - lease.issued_ns == 1_000
    assert lease.valid(now_ns=lease.issued_ns) is True


def test_knowledge_record_materialization_validates_confidence() -> None:
    record = KnowledgeRecord("subject-1", "carrier is healthy", 0.75, ("observation-1",), 1_000).materialize()

    assert record.record_id
    assert record.record_id == KnowledgeRecord(
        "subject-1", "carrier is healthy", 0.75, ("observation-1",), 1_000
    ).materialize().record_id

    with pytest.raises(ValueError):
        KnowledgeRecord("subject-1", "claim", 1.5, (), 1_000).materialize()


def test_decision_record_identity_is_derived_from_its_evidence() -> None:
    first = DecisionRecord.create("subject-1", "restart", "lease expired", evidence_ids=["e1"], policy_ids=["p1"], confidence=0.5)
    second = DecisionRecord.create("subject-1", "restart", "lease expired", evidence_ids=["e1"], policy_ids=["p1"], confidence=0.5)
    different = DecisionRecord.create("subject-1", "restart", "lease expired", evidence_ids=["e2"], policy_ids=["p1"], confidence=0.5)

    assert first.decision_id == second.decision_id
    assert first.decision_id != different.decision_id
    assert first.evidence_ids == ("e1",)
    assert first.policy_ids == ("p1",)


def test_decision_record_rejects_out_of_range_confidence() -> None:
    with pytest.raises(ValueError):
        DecisionRecord.create("subject-1", "restart", "reason", confidence=-0.1)
    with pytest.raises(ValueError):
        DecisionRecord.create("subject-1", "restart", "reason", confidence=1.1)


def test_world_state_snapshot_normalizes_and_stabilizes_identity() -> None:
    first = WorldStateSnapshot.create(["b", "a", "a"], ["o2", "o1"], generation=3)
    second = WorldStateSnapshot.create(["a", "b"], ["o1", "o2"], generation=3)

    assert first.objects == ("a", "b")
    assert first.observations == ("o1", "o2")
    assert first.snapshot_id == second.snapshot_id
    assert first.snapshot_id != WorldStateSnapshot.create(["a", "b"], ["o1", "o2"], generation=4).snapshot_id


def test_reconcile_reports_only_changed_keys_deterministically() -> None:
    assert reconcile({"a": 1, "b": 2}, {"a": 1, "b": 2}) == ()
    assert reconcile({"a": 1, "b": 2}, {"a": 1, "b": 3}) == ("b",)
    assert reconcile({"a": 1}, {"b": 2}) == ("a", "b")
    assert reconcile({"b": 2, "a": 1}, {}) == ("a", "b")


def test_safe_stop_records_reason_without_claiming_verification() -> None:
    result = safe_stop("subject-1", {"state": "running"}, {"state": "failed"}, reason="backend unavailable")

    assert isinstance(result, ControlLoopResult)
    assert result.safe_stop is True
    assert result.verified is False
    assert result.action is None
    assert result.decision_id is None
    assert result.reason == "backend unavailable"
    assert result.desired_state == {"state": "running"}
    assert result.observed_state == {"state": "failed"}
