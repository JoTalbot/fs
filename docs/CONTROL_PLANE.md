# FS Control Plane

The FS Control Plane is the authority that coordinates storage, execution, isolation, policy, snapshots, and recovery. It is deliberately separated from storage drivers and platform-specific adapters.

## Responsibilities

```text
                 FS CONTROL PLANE
  ┌─────────────────────────────────────────────┐
  │ object registry   policy engine   events    │
  │ desired state     health          recovery │
  │ scheduler         snapshots       secrets* │
  └───────────────┬─────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        v         v         v
    Storage     Runtime   Isolation
     engine     engine    backends
        │         │         │
        └─────────┼─────────┘
                  v
            Platform HAL
                  │
                  v
               Host OS
```

`secrets*` means references to an external secret provider, never plaintext key material stored in ordinary FS metadata.

## Desired state and reconciliation

FS uses a controller-style model:

1. user declares desired state;
2. control plane validates policy and capabilities;
3. current state is observed;
4. a reconciler computes the smallest required change;
5. workers perform the operation;
6. postconditions are verified;
7. resulting state and events are persisted redundantly.

This avoids treating a failed command as equivalent to successful state.

## Event model

Every state-changing operation produces an append-only event with:

- event UUID;
- object UUID and generation;
- actor identity;
- operation type;
- requested change;
- policy decision;
- start/end timestamps;
- result code;
- affected resources;
- integrity hash;
- correlation ID.

Events form an audit trail and are also recovery inputs.

## Idempotency

Control-plane operations should be idempotent whenever practical. Replaying an operation after a crash must converge toward the same desired state instead of duplicating resources.

Every externally visible mutation may carry an idempotency key. Workers verify the key against the operation journal before repeating non-idempotent work.

## Scheduler

The scheduler assigns work based on:

- dependencies;
- resource availability;
- failure domains;
- policy constraints;
- priority;
- deadlines;
- backend capabilities;
- current health.

The initial implementation may use a local priority queue. The API must not encode assumptions that prevent a future distributed scheduler.

## Health model

Health has two dimensions:

`desired_state` and `observed_state`.

An object can therefore be:

```text
desired=RUNNING
observed=DEGRADED
```

without falsely claiming success.

Health checks are typed:

- liveness: is the worker running;
- readiness: can it accept work;
- integrity: does stored state verify;
- capacity: can the object satisfy declared resources;
- dependency: are required objects healthy.

## Recovery

Recovery operates from the latest verified generation rather than blindly replaying all history.

Recovery precedence:

1. preserve evidence of failure;
2. isolate corrupt state;
3. identify the latest verified generation;
4. restore or reconstruct state;
5. validate postconditions;
6. publish the recovered generation;
7. record the recovery event.

## Control API shape

The reference API should eventually expose resource-oriented operations:

```text
GET    /v1/objects/{id}
POST   /v1/objects
PATCH  /v1/objects/{id}
POST   /v1/objects/{id}:start
POST   /v1/objects/{id}:stop
POST   /v1/objects/{id}:snapshot
POST   /v1/objects/{id}:recover
GET    /v1/objects/{id}/events
GET    /v1/capabilities
GET    /v1/health
```

Transport is intentionally abstract. Unix sockets, Windows named pipes, and future authenticated network transports can implement the same contract.

## Trust boundaries

The control plane is trusted to coordinate, not to bypass the host. Platform adapters are the only layer permitted to call host-specific APIs. Isolation backends provide stronger boundaries when required.

The strongest future configuration is:

```text
hardware
  -> boot/hypervisor layer (optional)
  -> FS control plane
  -> isolated environments
  -> host/guest operating systems
```

This is the route by which FS can become a genuine system layer without pretending a normal user-space process has magical kernel powers.
