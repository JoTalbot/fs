# FS Resource Mesh

The Resource Mesh is the long-term model for making FS adaptive across computers, disks, storage services, runtimes, and supported execution backends.

## Core idea

FS does not assume that one machine is the whole computer. It models usable capability as a graph:

```text
                     FS Control Plane
                            |
              +-------------+-------------+
              |             |             |
           local          trusted       approved
           node            peers        services
              |             |             |
        +-----+-----+   +---+---+    +----+----+
        |     |     |   |       |    |         |
      disk   CPU   VM  storage compute backup runtime
```

The logical environment is separated from placement. This makes migration, replication, failover, and resource balancing possible without changing the environment definition.

## Capability graph

Each node periodically publishes a signed capability snapshot containing only permitted metadata:

```text
Node
  -> capabilities
  -> resources
  -> health
  -> policy hints
```

The graph should support relationships such as:

- `hosts`
- `provides`
- `replicates`
- `depends_on`
- `reachable_via`
- `compatible_with`
- `failure_domain`

## Self-expansion loop

```text
OBSERVE
   -> DISCOVER PERMITTED CAPABILITIES
   -> VERIFY
   -> SCORE
   -> PLAN
   -> POLICY CHECK
   -> APPLY
   -> VERIFY RESULT
   -> RECORD
```

The loop is deliberately bounded by policy. Discovery can become broad; authority cannot silently become broad.

## Resource classes

### Storage

- local filesystem;
- removable storage;
- network storage explicitly configured for FS;
- remote FS node;
- virtual disk;
- snapshot/archive target.

### Compute

- local CPU/memory;
- trusted remote compute;
- container runtime;
- microVM runtime;
- VM runtime;
- accelerator exposed by a trusted backend.

### Services

A service can advertise an interface and requirements without exposing unrelated host internals.

### Connectivity

The mesh models connectivity as capabilities, including latency, bandwidth, reachability, and policy constraints.

## Placement strategy

The planner should optimize a weighted objective rather than one hard-coded rule:

```text
score = durability
      + availability
      + locality
      + performance
      + capacity
      + compatibility
      - latency
      - risk
      - policy cost
```

Exact weighting belongs to policy profiles.

## Automatic rebalancing

When a resource becomes unhealthy or overloaded:

```text
HEALTHY
  -> DEGRADED
  -> PLAN
  -> MIGRATE/REPLICATE
  -> VERIFY
  -> HEALTHY
```

No object is considered migrated until integrity and runtime health checks succeed.

## Multi-computer environment

An Environment can have a logical identity independent of its host:

```text
Environment E
  |
  +-- Workspace W
  +-- Volume V
  +-- Process P
  +-- Service S
  +-- Snapshot T
```

The planner can map these objects to different nodes while preserving the logical identity.

## Future directions

- peer-to-peer replication;
- distributed metadata quorum;
- remote execution broker;
- content-addressed object transport;
- zero-copy/locality-aware data movement where supported;
- live migration for compatible backends;
- heterogeneous compute scheduling;
- automatic capacity balancing;
- offline-first federation with later reconciliation;
- federation-wide snapshots;
- disaster recovery across independent failure domains.

## Hard boundary

The mesh is an explicit federation layer. It is not a mechanism for covert discovery, persistence, privilege escalation, credential harvesting, or control of machines that have not joined or authorized the federation.
