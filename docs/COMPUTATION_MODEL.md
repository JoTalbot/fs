# FS Computation Model

## Purpose

The Computation Model defines a universal state-transition abstraction shared by files, processes, applications, environments, Computers and Worlds.

FS computation is modeled as a verified transition rather than as an assumption that a backend call succeeded.

## Core Form

`Transition = (Intent, Preconditions, Inputs, Operations, Effects, Postconditions, Evidence)`

An executable transition is valid only when:

- its preconditions are satisfiable;
- required capabilities are available;
- authority is sufficient;
- resources are admitted;
- dependencies are resolved;
- policy constraints are satisfied;
- the selected backend implements the required semantics.

## Operation Contract

Every semantic operation has:

- operation id
- target ObjectID(s)
- input references
- required capabilities
- authority scope
- resource requirements
- preconditions
- expected effects
- postconditions
- timeout/deadline semantics
- idempotency/retry semantics
- compensation strategy where applicable
- provenance context

## Plan DAG

A plan is represented as a directed acyclic graph of bounded operations whenever ordering permits. Each node declares inputs, outputs, dependencies and verification conditions.

The planner may execute independent nodes concurrently when resource, dependency, policy and backend semantics permit it.

Cycles are not silently flattened. They are represented as explicit coordination requirements or rejected as infeasible.

## Transaction Boundary

A plan node or coordinated group enters the Transaction Engine before critical state changes:

`VALIDATE -> RESERVE -> PREPARE -> APPLY -> VERIFY -> COMMIT`

Failure produces compensation, recovery or a safe-stop state according to the declared transition contract.

## State Transition Semantics

The authoritative state change is represented by an event only after the applicable verification boundary is satisfied. Observations remain distinguishable from requested effects.

## Idempotency

Operations that may be retried must declare idempotency semantics. Non-idempotent operations require stronger transaction/recovery handling and must not be blindly repeated.

## Recursive Computation

A World transition may contain Computer transitions; a Computer transition may contain Environment transitions; an Environment transition may contain Application transitions; and an Application transition may contain process or resource transitions.

The semantic contract remains the same across levels while the concrete backend changes.

## Determinism

Where deterministic execution is possible, inputs, versions, policies, decisions and event ordering are captured so the transition can be replayed. Where nondeterminism is inherent, it is recorded as evidence rather than hidden.
