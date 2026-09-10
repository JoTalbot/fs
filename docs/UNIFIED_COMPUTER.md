# FS Unified Computer

## Status

Architectural specification for the next major FS layer.

## Purpose

FS SHALL be able to present a **single logical computer** backed by multiple explicitly admitted physical nodes and resources. The logical computer is stable even when its physical composition changes.

The goal is a unified computing experience, not a false claim that arbitrary heterogeneous machines become one physically coherent NUMA computer.

## Core model

```text
FS World
    |
    v
FS Computer
    |
    +-- Unified Resource Fabric
    |     +-- CPU compute pool
    |     +-- Memory tiers
    |     +-- Storage pool
    |     +-- GPU / accelerator pool
    |     +-- Network fabric
    |     +-- Device fabric
    |
    +-- Universal Runtime
    |     +-- native
    |     +-- container / sandbox
    |     +-- microVM
    |     +-- VM
    |
    +-- Unified Desktop / Session
    |
    +-- Policy + Security + Recovery
    |
    +-- Physical Nodes
```

## First-class Computer object

A Computer is a persistent logical FS object with:

- `ComputerID` independent of physical location;
- desired and actual state;
- member nodes;
- CPU, memory, storage, GPU, network and device resource pools;
- runtime catalog and compatibility matrix;
- placement and admission policies;
- failure domains;
- health and capacity state;
- sessions and desktop integration;
- snapshots, recovery and migration metadata;
- policy references and immutable history.

Physical nodes are replaceable members, not the identity of the computer.

## Unified Resource Fabric

The fabric pools resources without pretending that heterogeneous resources have identical characteristics.

### CPU

CPU is represented as **schedulable logical compute capacity**. Ordinary interactive applications normally execute on one suitable node or guest environment. Workloads explicitly capable of decomposition may be represented as task graphs and scheduled across multiple nodes.

FS MUST NOT claim transparent distribution of arbitrary machine instructions across unrelated hosts.

### Memory

Memory is hierarchical rather than magically coherent across hosts:

```text
local RAM -> nearby RAM -> remote RAM -> persistent storage
```

Placement, caching, checkpointing, paging and migration may exploit these tiers. Special distributed-memory runtimes may provide stronger semantics to applications designed for them.

### Storage

Storage can be presented much more transparently as a logical pool. Physical SSD, NVMe, HDD, NAS and other admitted backends provide capacity subject to policy, locality, durability and failure-domain constraints.

The logical storage identity remains stable while shards and replicas move.

### GPU and accelerators

Accelerators are assignable resources with explicit compatibility and locality constraints. Supported runtimes may use passthrough, partitioning, remote execution or other backend-specific mechanisms.

### Network

Network is modeled as a fabric with latency, bandwidth, reachability, isolation and policy constraints. Placement decisions account for data locality and communication cost.

### Devices

Display, keyboard, pointer, audio, microphone, camera, USB and other devices are represented through a capability-controlled device layer. Device exposure is explicit and revocable.

## Universal Runtime

FS SHALL expose one execution API while selecting an appropriate backend.

```text
Application
    |
    v
Universal Execution API
    |
    v
Compatibility + Policy + Resource Planner
    |
    +-- Native
    +-- Container/Sandbox
    +-- MicroVM
    +-- VM
```

Supported application families can include Linux ELF, Windows applications, Android packages, BSD environments, WebAssembly and native FS applications, provided an appropriate runtime exists.

The runtime selection process considers architecture, OS requirements, GUI requirements, device needs, isolation, resources, migration support and policy.

## Application classes

1. **Native**: application runs directly on a compatible admitted node.
2. **Virtualized**: application runs inside a container, sandbox, microVM or VM.
3. **Distributed**: application or workload is explicitly decomposed into tasks that may run across multiple nodes.

FS MUST NOT silently transform an arbitrary ordinary process into a distributed process when its runtime semantics do not support that transformation.

## Universal Application Manifest

An FS application may declare:

- application identity and version;
- supported architectures and operating systems;
- runtime requirements;
- interactive/headless mode;
- CPU, memory, GPU and storage requirements;
- filesystem scope;
- network requirements;
- device requirements;
- migration/checkpoint support;
- recovery behavior;
- security permissions;
- package provenance and signatures.

This allows FS to plan execution before launch rather than discovering incompatibility after failure.

## Application identity and mobility

A logical application identity is independent of its current process placement.

```text
ApplicationID
    |
    +-- Instance on Node A
    +-- Instance in VM on Node B
    +-- Checkpoint / snapshot
```

Where the runtime supports checkpointing or migration, FS may move an instance while preserving its logical identity, attached state and storage references.

## Unified Desktop

A future FS desktop SHALL present applications as part of one logical session even when applications execute in different environments or nodes.

The desktop layer may provide:

- window/session composition;
- clipboard;
- logical filesystem access;
- notifications;
- audio routing;
- display routing;
- input routing;
- application lifecycle controls.

Remote GUI transport is an implementation detail and MUST remain policy-controlled.

## Hot-plug of resources

Nodes may join or leave the Computer dynamically.

### Admission

```text
DISCOVER
  -> VERIFY IDENTITY
  -> TRUST POLICY
  -> CAPABILITY NEGOTIATION
  -> RESOURCE ADMISSION
  -> HEALTH CHECK
  -> JOIN
```

A discovered node contributes no resources until explicitly admitted by policy.

### Departure or failure

```text
DETECT
  -> ASSESS IMPACT
  -> REPLAN
  -> MIGRATE / REPLICATE / RECONSTRUCT
  -> VERIFY
  -> RESUME
```

The Computer remains logically present even when physical members disappear, subject to available capacity and recovery guarantees.

## Resource-aware placement

Placement SHOULD consider:

- compatibility;
- CPU capacity;
- memory capacity and tier latency;
- accelerator availability;
- storage locality;
- network latency/bandwidth;
- failure-domain diversity;
- health;
- energy state;
- policy constraints;
- workload priority;
- migration cost;
- recovery requirements.

Interactive workloads favor latency and local devices. Batch workloads favor throughput and capacity. Distributed workloads favor data locality and communication efficiency.

## Session mobility

A user session is a first-class logical object. Where supported, FS can checkpoint or migrate environments and applications while retaining:

- session identity;
- workspace references;
- persistent data;
- application identity;
- environment metadata;
- recovery state.

The system MUST clearly distinguish full migration, checkpoint/restore and restart-with-state from mere relaunch.

## Logical hardware profile

FS MAY expose a stable virtual hardware profile to compatible guest environments. The profile MUST be honest about capabilities and MUST NOT advertise resources that are unavailable or unauthorized.

Physical heterogeneity is hidden behind adapters, not denied by fiction.

## Failure and recovery

The Computer participates in the global reconciliation model:

```text
DESIRED COMPUTER
      |
      v
OBSERVE ACTUAL
      |
      v
DETECT DRIFT
      |
      v
PLAN
      |
      v
POLICY CHECK
      |
      v
TRANSACTION
      |
      v
VERIFY
      |
      v
COMMIT HISTORY
```

High-impact migration, resource reconfiguration and runtime changes SHOULD support simulation or shadow planning before execution.

## Security boundaries

The Unified Computer does not weaken the FS security model.

- Node discovery is not trust.
- Admission is explicit.
- Capabilities are scoped.
- Secrets are referenced, not embedded.
- Learning cannot grant authority.
- Remote execution requires authorization.
- Device exposure is explicit.
- High-impact actions are attributable, bounded, reversible where possible and audited.
- Uncertain operations fail closed.
- No covert persistence, hidden system-wide discovery, privilege escalation or silent modification of unrelated host data.

## User-facing model

The intended experience is conceptually:

```text
fs status

FS Computer: personal
CPU:      logical compute capacity
Memory:   hierarchical pool
Storage:  unified pool
GPU:      available accelerators
Nodes:    admitted resources
Runtime:  native/container/microVM/VM
```

And:

```text
fs run firefox
fs run application.exe
fs run linux-app
fs run android-app
fs vm linux
fs vm windows
```

These commands express intent. The planner chooses an authorized execution environment and placement.

## Architectural invariant

**One logical computer does not require one physical machine.**

FS therefore separates:

```text
Logical identity
    !=
Physical placement
```

and:

```text
Unified experience
    !=
False physical uniformity
```

This distinction is foundational to the FS architecture.