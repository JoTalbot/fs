from fs_overlay.core import (
    Idempotency,
    Operation,
    PlanDAG,
    PlanNode,
    ReferenceSimulationBackend,
    StateTransition,
)


def op(name: str) -> Operation:
    return Operation(
        operation_id=name,
        target="obj:test",
        preconditions=("ready",),
        effects=("changed",),
        postconditions=("verified",),
        idempotency=Idempotency.IDEMPOTENT,
    )


def test_plan_dag_validates_and_detects_cycles():
    plan = PlanDAG(
        nodes=(
            PlanNode("a", op("a")),
            PlanNode("b", op("b"), frozenset({"a"})),
        )
    )
    assert plan.validate() == ()

    cycle = PlanDAG(
        nodes=(
            PlanNode("a", op("a"), frozenset({"b"})),
            PlanNode("b", op("b"), frozenset({"a"})),
        )
    )
    assert "plan contains dependency cycle" in cycle.validate()


def test_transition_requires_explicit_contract():
    transition = StateTransition("t1", "obj", "READY", "start", (), ("run",), (), "ACTIVE")
    errors = transition.validate()
    assert "missing preconditions" in errors
    assert "missing postconditions" in errors


def test_simulation_never_claims_host_mutation():
    result = ReferenceSimulationBackend().execute(op("simulate"))
    assert result.can_commit()
    assert "no-host-mutation" in result.evidence


def test_unknown_idempotency_is_rejected_by_plan_validation():
    operation = Operation(
        operation_id="unsafe-retry",
        target="obj:test",
        preconditions=("ready",),
        effects=("changed",),
        postconditions=("verified",),
    )
    errors = PlanDAG((PlanNode("x", operation),)).validate()
    assert "x: idempotency is unknown" in errors
