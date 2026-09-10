# FS Transaction Engine

## Purpose

The Transaction Engine coordinates atomic or compensatable changes across Data, Compute, Control and Resource spaces. It prevents the control plane from declaring success before the resulting state has been verified.

## Transaction lifecycle

```text
BEGIN
  -> VALIDATE
  -> RESERVE
  -> PREPARE
  -> APPLY
  -> VERIFY
  -> COMMIT

Failure at any reversible stage
  -> COMPENSATE / ROLLBACK
  -> VERIFY RECOVERY
```

## Scope

Transactions may cover storage mutations, metadata changes, resource reservations, environment lifecycle, process/service changes, migration, replication, snapshots and policy transitions.

Not every operation can be physically rolled back. Such operations must declare their compensation or recovery semantics before execution.

## Invariants

1. No critical commit without verification.
2. Every transaction has an identity, initiator, policy context and target set.
3. Prepared state is distinguishable from committed state.
4. Partial failure is represented explicitly, never hidden as success.
5. Recovery references the last verified state.
6. Cross-node transactions require explicit trust and failure semantics.
7. Transaction records are append-oriented and auditable.
8. Transaction authority is bounded by the caller's policy and resource leases.

## Transaction record

```text
transaction_id
actor
policy_version
targets
pre_state
intended_state
reservations
operations
verification
result
compensation
rollback_reference
causal_context
```

## Relationship to reconciliation

Reconciliation proposes and executes desired-state transitions. The Transaction Engine supplies the commit boundary. Reality Engine observations verify the resulting actual state. Time Fabric supplies causal context.

```text
Intent -> Planner -> Transaction -> Runtime/Storage
                         |
                         v
                  Reality Engine
                         |
                         v
                    Verified State
```
