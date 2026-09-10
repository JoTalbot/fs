# FS World State Model

## Purpose

`WorldState(t)` is the explicit, versioned model of a bounded FS World at a logical point in time. It supports reconciliation, simulation, replay, consequence analysis and recovery planning.

## State Domains

`WorldState = Objects + Resources + Capabilities + Dependencies + Policies + Authorities + Leases + Executions + Observations + Events + Provenance + Health + Topology`

Each domain remains semantically distinct even when represented in one snapshot.

## Time

A state snapshot is associated with causal/logical ordering and observation metadata. Wall-clock timestamps are evidence, not the sole ordering mechanism.

## Transitions

World state evolves through attributed events and verified transactions. Desired state is never treated as actual state until observation and verification establish the declared semantics.

## Deterministic Replay

Given the required immutable event history, versions, policy references and deterministic inputs, the system should be able to reconstruct a historical logical state or simulate a proposed transition without mutating live reality.

## Branching

Simulation and what-if operations may create derived state branches. Branches are explicitly labeled and cannot affect live state unless promoted through the normal policy, authority and transaction path.

## Scope

A World State belongs to an explicit World boundary. It does not automatically encompass every visible host, network resource or discovered node.
