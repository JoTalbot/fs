# FS Resource Ownership & Lease Layer

## Purpose

The Resource Ownership Layer turns discovered capabilities into explicitly governed, time-bounded reservations and leases. Discovery describes what exists; ownership determines what FS is currently authorized to allocate.

## Model

```text
Intent
  -> Meta Scheduler
  -> Admission
  -> Resource Ownership
       -> Reservation
       -> Lease
       -> Quota
       -> Priority
       -> Delegation
  -> Resource Fabric
```

A resource may be discovered without being allocatable. Allocation requires identity, capability verification, policy admission and an ownership record.

## Invariants

1. A resource cannot be committed to incompatible owners simultaneously.
2. A lease has an owner, scope, authority, start condition, expiry/renewal policy and audit identity.
3. Expiry releases authority unless an explicit renewal succeeds.
4. Lost control-plane connectivity must not silently create indefinite ownership.
5. Resource accounting is separate from physical identity and placement.
6. Delegated authority cannot exceed the delegator's authority.
7. Preemption is policy-controlled and must preserve transactional state.
8. Ownership changes are event-recorded and verifiable.
9. Uncertain ownership state enters a safe/degraded mode rather than guessing.

## Resource lifecycle

```text
DISCOVERED -> VERIFIED -> ADMITTED -> RESERVED -> LEASED -> IN_USE
                                      |          |
                                      +----------+-> RELEASED
                                                   -> EXPIRED
                                                   -> REVOKED
                                                   -> QUARANTINED
```

## Resource classes

The layer is resource-type agnostic. It may govern CPU capacity, memory tiers, storage capacity, GPU/accelerator capacity, network bandwidth, devices, runtime slots and virtual resources.

## Failure handling

A lease is not proof that the underlying resource is healthy. Reality observations continuously reconcile ownership with actual resource state. On node loss or uncertain state, FS marks the lease affected, prevents unsafe reassignment, then recovers or reclaims according to policy.

## Distributed ownership

Cross-node leases require explicit federation trust and a conflict-resolution protocol. The design must avoid a hidden single authority assumption. Future implementations may use quorum-backed ownership records, fencing tokens and monotonic lease generations.

## Safety boundary

Ownership is valid only inside explicitly admitted FS resources and policies. The layer never bypasses host access controls or silently claims resources outside the federation boundary.
