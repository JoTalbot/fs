# FS State Machine Engine

## Purpose

The State Machine Engine provides one lifecycle model for all managed FS objects while allowing object-specific states and transitions.

## Common lifecycle

```text
NEW
 -> DISCOVERED
 -> PREPARED
 -> ACTIVE
 -> DEGRADED
 -> RECOVERING
 -> ACTIVE
 -> MIGRATING
 -> ACTIVE
 -> RETIRED
```

Objects may enter `FAILED`, `QUARANTINED` or other typed states where their contract requires them.

## Applicable objects

The engine can represent files, shards, carriers, volumes, processes, services, applications, environments, nodes, resources, devices, networks, snapshots, packages and Computers.

## Transition contract

A transition declares:

- source state;
- target state;
- preconditions;
- required capabilities;
- policy requirements;
- resource requirements;
- transaction boundary;
- observable verification criteria;
- compensation/recovery path.

A transition is not complete merely because an operation returned successfully. Actual state must be observed and verified.

## Desired versus actual

The engine does not collapse desired state into actual state. Desired state requests a transition; Reality Engine observations establish whether the transition occurred.

## Failure semantics

Failure is a first-class state. When confidence or integrity is insufficient, the engine preserves the last verified state, records the failed transition and enters a safe/degraded/quarantined state as appropriate.

## Recursive composition

A Computer, Environment or Workspace may contain child state machines. Parent transitions constrain child transitions, while child components cannot silently expand parent authority.

## Future implementation

State definitions and transition policies should be declarative and versioned. The engine should support deterministic replay, transition validation, property-based testing and simulation before high-impact autonomous transitions.
