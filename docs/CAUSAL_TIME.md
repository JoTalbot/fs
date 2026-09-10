# FS Causality & Time Fabric

## Purpose

FS Time Fabric provides a platform-neutral temporal model for local and distributed operation. It separates physical time from monotonic measurement, logical ordering and causal relationships.

## Layers

```text
Physical / wall-clock time
        |
Monotonic time
        |
Logical time
        |
Causal relationships
        |
Distributed event ordering
        |
FS history / replay / recovery
```

Wall-clock time is useful for human-facing timestamps and deadlines, but it is not the sole authority for ordering distributed events.

## Event model

Every causally relevant event should be identifiable and, where required, carry:

- event identity;
- actor/object identity;
- logical time or sequence;
- parent/causal references;
- observed physical timestamp when available;
- policy/version context;
- provenance;
- verification state.

## Guarantees

The Time Fabric should allow FS to distinguish:

- before;
- after;
- concurrent;
- causally dependent;
- uncertain ordering.

It must never manufacture causal certainty from synchronized-looking wall-clock timestamps alone.

## Uses

Time Fabric supports event sourcing, deterministic replay, snapshots, migration, reconciliation, distributed recovery, transaction ordering, simulation and Digital Twin scenarios.

## Failure and partition behavior

Clock skew, offline operation and network partitions are expected conditions. Local progress may continue where policy allows, while reconciliation uses causal metadata and explicit conflict rules. Ambiguous high-impact ordering must fail closed or enter a recoverable degraded state.

## Future implementation

The implementation may combine monotonic local sequence numbers, Lamport-style logical clocks, vector/causal metadata where needed, signed event records and snapshot checkpoints. The concrete mechanism remains replaceable behind the Time Fabric contract.
