# FS Plan DAG

## Purpose

The Plan DAG is the intermediate representation between intent/decision and transactional execution.

## Node Model

Each plan node contains:

- PlanNodeID
- semantic operation
- target references
- inputs and outputs
- dependency edges
- capability requirements
- authority scope
- resource requirements
- policy constraints
- expected effects
- verification conditions
- retry/idempotency policy
- compensation/recovery policy
- provenance

## Edge Types

- `depends_on`: predecessor must complete first
- `produces`: predecessor creates an input for another node
- `reserves`: resource reservation dependency
- `conflicts`: operations cannot overlap
- `coordinates`: shared synchronization boundary
- `verifies`: verification relationship

## Planning Rules

1. Feasibility is evaluated before optimization.
2. Required dependencies must be satisfied explicitly.
3. Independent nodes may run concurrently only when isolation and resource constraints permit it.
4. A plan cannot contain an operation whose authority exceeds the parent intent scope.
5. The planner must preserve required semantics when selecting or replacing a backend.
6. Uncertainty is represented explicitly and may force simulation, human approval or safe-stop.

## Plan Lifecycle

`Draft -> Validated -> Admitted -> Simulated/Shadowed -> Approved -> Executing -> Verified -> Committed`

Alternative terminal states include `Rejected`, `Cancelled`, `Failed`, `Compensating`, `Recovered` and `Expired`.

## Promotion

A plan is not reality. Only verified execution through the transaction/runtime path can produce live state changes.
