# FS Execution Semantics

## Purpose

Execution Semantics defines what it means for FS to execute an abstract operation across different backends while preserving observable behavior and declared guarantees.

## Abstract execution

```text
Semantic Operation
   -> Capability Check
   -> Authority Check
   -> Compatibility Check
   -> Resource Admission
   -> Backend Selection
   -> Transaction
   -> Execution
   -> Observation
   -> Verification
```

The backend may be native, sandboxed, containerized, microVM-based, VM-based or distributed when the workload contract permits it.

## Execution contract

An operation declares:

- inputs;
- target objects;
- required capabilities;
- required authority;
- resource requirements;
- isolation requirements;
- expected observable effects;
- recovery/rollback semantics;
- migration/checkpoint semantics where supported.

## Observable semantics

Portability does not mean identical implementation. FS guarantees only the behaviors explicitly represented by the application/environment contract and verified by the selected backend.

An operation that cannot preserve its declared semantics must not be silently translated into a weaker behavior.

## Mobility

Application and Environment identity remain logical. If checkpoint/restore or migration is supported and verified, execution may move between compatible backends without changing logical identity.

## Distributed execution

Distribution is opt-in through workload semantics and compatibility. Ordinary applications are not silently split across machines merely because resources exist there.

## Recovery

After execution, Reality Engine observations determine actual state. Failed verification returns the object to a recoverable state or triggers a declared recovery transition.
