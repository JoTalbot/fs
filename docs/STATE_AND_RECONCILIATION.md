# State, Intent and Reconciliation

FS treats desired state and actual state as separate first-class concepts.

## Object state envelope

Every managed object should expose:

```text
ObjectID
Kind
Generation
DesiredState
ActualState
Health
Location
Capabilities
Dependencies
PolicyRefs
HistoryRefs
```

This model applies uniformly to files, shards, carriers, volumes, processes, services, environments, nodes and resources.

## Reconciliation loop

```text
observe actual state
       ↓
load desired state
       ↓
detect drift
       ↓
construct candidate plans
       ↓
validate policy/capabilities
       ↓
estimate risk and resource cost
       ↓
optional shadow simulation
       ↓
execute transaction
       ↓
verify resulting state
       ↓
commit event/state
```

A failed or uncertain transition must preserve the last verified state and enter an appropriate degraded or recovery path.

## Hierarchical reconciliation

Reconciliation is hierarchical:

```text
FS World
  └─ Site
      └─ Node
          └─ Environment
              └─ Workload
                  └─ Volume
                      └─ Object
                          └─ Shard
                              └─ Carrier
```

A failure higher in the hierarchy can trigger reconciliation below it. A lower-level repair must not silently violate higher-level policy.

## Transaction model

Critical changes use a transactional lifecycle:

```text
PLAN → PREPARE → CHECKPOINT → APPLY → VERIFY → COMMIT
                              │
                              └──── failure → ROLLBACK/RECOVERY
```

Operations should be idempotent where practical. Commit requires verification of integrity, policy, compatibility, and resource constraints.

## Explainability

Every autonomous transition should expose why it was selected, what alternatives were rejected, what policy permitted it, what resource budget was consumed, and how the result was verified.

## Shadow and simulation

High-impact changes should support a shadow planner that evaluates the intended transition against a simulated state before applying it. Simulation is advisory until the real system verifies the transition.

## Safe stop

When state is ambiguous, trust is insufficient, integrity cannot be verified, or a policy boundary is unclear:

```text
STOP
PRESERVE VERIFIED STATE
RECORD EVENT
WAIT / REQUEST AUTHORIZATION / RECOVER
```
