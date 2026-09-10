# FS Bounded Autonomy

## Goal

FS should be capable of continuously improving placement, resilience, runtime selection, and recovery without requiring a human to supervise every routine operation.

Autonomy means continuous reconciliation inside a declared authority boundary. It does not mean unrestricted access to the host or surrounding network.

## Autonomy levels

```text
L0 OBSERVE
  report only

L1 SUGGEST
  produce plans, no mutations

L2 POLICY-AUTO
  execute pre-approved low-risk operations

L3 FEDERATED-AUTO
  operate across explicitly trusted FS nodes

L4 SYSTEM-AUTO
  manage approved isolated environments and VM guests
```

The active level is part of signed configuration and is visible to the operator.

## Decision loop

```text
state -> detect drift -> generate candidates -> validate policy
      -> choose plan -> execute transaction -> verify -> record
```

Every action has:

- actor identity;
- policy identity/version;
- target object;
- reason;
- before state;
- intended state;
- result;
- verification result;
- rollback information when available.

## Autonomous opportunities

FS can automatically optimize:

- storage placement;
- shard distribution;
- replication factor;
- snapshot retention;
- workspace locality;
- runtime backend selection;
- resource allocation within limits;
- failed service restart;
- environment migration between trusted nodes;
- cache placement;
- disaster-recovery preparation.

## Learning without unsafe authority expansion

Historical telemetry can improve planning models, but learned behavior cannot grant itself new permissions. A policy change must remain an explicit configuration event.

## Resource discovery

FS may discover permitted peers and capabilities, classify them, and maintain a changing resource graph. Newly discovered resources begin in an untrusted state and cannot receive workloads or data until policy authorizes them.

## Failure behavior

When a decision is uncertain or verification fails, the safe default is:

```text
STOP -> PRESERVE STATE -> RECORD -> REQUEST/WAIT
```

The system should prefer degraded service over an unverified destructive action.

## Long-term objective

The autonomous control plane should make an FS Environment portable across heterogeneous machines while keeping the logical identity, state, policy, storage integrity, and recovery model stable.
