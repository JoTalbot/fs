# FS Reality Engine

## Purpose

The Reality Engine is the observation and reconciliation layer between the logical FS model and physical or virtual reality.

FS must never confuse desired state with observed state.

## Model

```text
Desired State
     |
     v
Reality Engine
     |
     +--> Observe hardware
     +--> Observe nodes
     +--> Observe resources
     +--> Observe runtimes
     +--> Observe environments
     +--> Observe applications
     +--> Observe storage
     +--> Observe network
     |
     v
Actual State
     |
     v
Object Graph
```

## Observation pipeline

```text
COLLECT
  -> AUTHENTICATE SOURCE
  -> NORMALIZE
  -> VALIDATE
  -> CORRELATE
  -> UPDATE ACTUAL STATE
  -> DETECT DRIFT
```

Observations carry source identity, timestamp information, capability context, confidence and provenance.

## Reality versus model

An object can simultaneously have:

```text
desired_state = RUNNING
actual_state  = STOPPED
health        = DEGRADED
```

This is not an error in the model. It is precisely the condition reconciliation exists to resolve.

## Drift classes

FS should distinguish at least:

- missing object;
- unexpected object;
- changed capability;
- changed placement;
- changed content;
- changed runtime;
- resource exhaustion;
- health degradation;
- policy drift;
- topology drift;
- version incompatibility;
- incomplete transaction.

## Confidence

Observations may have confidence levels. High-impact actions must not rely on weak or stale observations when stronger verification is available.

A low-confidence state can force:

```text
SAFE / DEGRADED
    -> PRESERVE LAST VERIFIED STATE
    -> RECORD UNCERTAINTY
    -> WAIT FOR BETTER OBSERVATION
```

## Reality snapshots

The engine should produce immutable, content-addressed snapshots of the observed FS world. Snapshots support:

- audit;
- comparison;
- replay;
- time travel;
- simulation inputs;
- recovery planning;
- debugging;
- incident reconstruction.

## Reconciliation contract

```text
observe(actual)
load(desired)
compare()
produce(candidate plans)
apply(policy)
verify()
commit(observed result)
```

A plan is not reality until verification succeeds.

## External reality changes

FS must expect external changes. Examples include a user changing a file, an administrator stopping a service, a node losing power, a network route disappearing, or hardware becoming unavailable.

Unexpected changes are classified rather than silently overwritten. Critical mutations can enter quarantine or require a new reconciliation transaction.

## Digital-twin integration

The Reality Engine is the source of verified observations for the FS Digital Twin. The Digital Twin may then execute what-if scenarios against a copy of the state without mutating production reality.

## Event sourcing

Every important state transition should produce an immutable event with:

```text
event_id
object_id
object_generation
source_node
correlation_id
observed_at
logical_order
before_state
after_state
provenance
verification
```

Events are evidence of transitions, not permission to perform them.

## Recovery

When reality diverges from desired state, recovery is selected by policy and capability:

```text
DRIFT
  -> IMPACT ASSESSMENT
  -> CANDIDATE RECOVERY
  -> POLICY CHECK
  -> OPTIONAL SIMULATION
  -> TRANSACTION
  -> VERIFY
  -> RESUME OR SAFE-STOP
```

The engine must preserve the last verified state when recovery cannot be established safely.
