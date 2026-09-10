# Resource Intelligence

Resource Intelligence is the layer that turns raw capability advertisements into safe placement and recovery decisions.

## Capability graph

A node does not merely expose resources. It exposes signed, policy-filtered capabilities:

```text
Node
 ├─ CPU
 ├─ Memory
 ├─ Storage
 ├─ GPU
 ├─ Network
 ├─ Device
 └─ Runtime
```

Relationships may include:

```text
provides
hosts
requires
compatible_with
replicates
reachable_via
failure_domain
```

Discovery is descriptive. Trust and authorization remain separate decisions.

## Placement factors

A placement plan can consider:

- durability;
- availability;
- locality and data gravity;
- capacity;
- performance;
- compatibility;
- latency and bandwidth;
- failure-domain diversity;
- energy and thermal state;
- resource cost;
- trust level;
- policy constraints.

The objective is not simply maximum performance. FS should optimize the declared policy objective while staying inside authority and resource budgets.

## Reservations and leases

Resources may be reserved or leased:

```text
reservation:
  resource: gpu
  owner: environment-A
  window: ...

lease:
  capability: device.use
  owner: workload-B
  expires: ...
```

Expired leases release resources automatically. Lease creation and revocation are auditable.

## Priority and autonomy budgets

Workloads can have priorities. Autonomous actions can have budgets such as:

```text
max_storage_movement
max_migrations
max_network_usage
max_cpu_overhead
max_concurrent_repairs
```

The planner must refuse a plan that exceeds its policy budget.

## Predictive resource intelligence

Historical health, utilization and failure signals may be used to predict risk and improve placement. Prediction cannot create authority or override policy.

## Energy and thermal awareness

Energy, battery and thermal constraints are resource attributes. A policy may prefer performance, balanced operation, or energy conservation.

## Data gravity

FS should compare the cost of moving data with the cost of moving computation. Large datasets should normally keep computation close to data when policy and trust permit it.

## Explainable decisions

Every placement decision should be inspectable:

```text
selected target
why selected
constraints satisfied
alternatives considered
risk/confidence
estimated movement/cost
policy references
```
