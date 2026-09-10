# FS — Portable System Substrate

FS starts as a user-controlled, failure-tolerant storage overlay and is designed to grow into a portable system control plane.

The long-term goal is not merely to hide more bytes inside files. It is to make **storage, workspaces, processes, services, environments, isolation, snapshots, policy and recovery parts of one coherent system model**.

> **Safety boundary:** FS never silently scans or modifies the whole operating system. Carrier roots and managed workspaces are explicitly configured, protected/system paths are denied, and mutations are attributable and auditable.

## Local storage spine

The reference engine provides a concrete, dependency-free storage path:

```text
input
  -> deterministic chunks
  -> content-addressed chunk objects
  -> immutable manifest
  -> durable journal visibility
  -> replayable inventory
  -> audit / recovery
  -> immutable snapshots
```

Implemented primitives include versioned manifests, deterministic fixed-size chunking, SHA-256 content addressing, atomic temporary-file replacement, replayable journal-backed inventory, transaction begin/commit/abort visibility, Merkle roots, structured events, immutable snapshots, deterministic recovery graphs, failure-domain-aware carrier ranking, and quarantine records.

`StorageTransaction` stages immutable data and publishes metadata only after a durable transaction commit marker. Recovery ignores transactions without that marker.

The HMAC development envelope is **integrity-only** and is deliberately not presented as encryption. Production confidentiality requires an audited AEAD provider. Erasure coding likewise remains an explicit provider interface until an audited implementation is selected.

## Resilience model

The storage layer distinguishes:

- **HEALTHY** — full configured redundancy is present;
- **DEGRADED** — enough shards remain for recovery, but redundancy is below target;
- **REPAIRING** — an approved repair is being executed;
- **UNRECOVERABLE** — fewer than the required data-shard threshold remains.

Snapshots contain object identities and a deterministic Merkle root rather than another copy of the data. Recovery dependencies are ordered explicitly by `RecoveryGraph`; cycles are rejected. Carrier selection consumes approved/healthy carrier facts and failure-domain information, while a plan itself never grants authority to mutate a carrier. Unexpected carrier changes are recorded in a quarantine ledger rather than silently overwritten.

See `docs/STORAGE_RESILIENCE.md` for the durability and recovery contract.

## One object model

FS treats resources as typed objects:

`File`, `Directory`, `Workspace`, `Volume`, `Container`, `Process`, `Service`, `Environment`, `Snapshot`, `Device`, `Network`, `Package`, `Policy`.

An environment can therefore be inspected and recovered as one graph rather than as an unrelated collection of files and processes.

## Control plane

```text
                 FS CONTROL PLANE
     policy · identity · objects · events
      desired state · health · recovery
                    |
          +---------+---------+
          v         v         v
       Storage    Runtime   Isolation
        engine     engine    backends
          |         |         |
          +---------+---------+
                    v
                 FS HAL
                    |
                 Host OS
```

The control plane uses declarative desired state and reconciliation. Operations are idempotent where practical, verified after execution, and recorded as structured events.

## Adaptive execution

FS discovers actual machine capabilities rather than assuming a fixed operating-system matrix. An environment can request:

```yaml
runtime: auto
policy:
  filesystem: workspace-only
  network: deny
```

The planner selects the least powerful backend that satisfies the declared policy, progressing from native execution to containers, microVMs or full VMs when available and required.

## System-in-system direction

The architecture evolves through levels:

```text
L0  storage overlay
L1  managed native processes
L2  sandbox/container workloads
L3  microVM workloads
L4  full VM environments
L5  FS-native environments and boot integration
```

The host OS remains fully functional in normal mode. Stronger isolation or control is achieved through explicit platform mechanisms such as containers, sandboxes, microVMs, VMs and eventually boot/hypervisor integration.

## Distributed future

The same object model is intended to work across multiple nodes. Storage and execution placement can become failure-domain aware while keeping logical object identity stable.

This gives FS a path from local storage overlay to a portable **system substrate** capable of orchestrating storage, execution and recovery across heterogeneous machines.

## CLI

```text
fs-overlay genesis ping
fs-overlay genesis capabilities
fs-overlay storage audit <root>
fs-overlay storage recover <root>
fs-overlay storage snapshot <root> --generation 1 --metadata purpose=checkpoint
```

Storage commands operate only on the explicitly supplied storage root.

## Repository layout

- `docs/ARCHITECTURE.md` — normative storage architecture and invariants
- `docs/STORAGE_RESILIENCE.md` — durability, snapshots, recovery, placement and quarantine model
- `docs/FORMAT.md` — FSOV carrier and manifest format
- `docs/OBJECT_MODEL.md` — unified managed-object model
- `docs/CONTROL_PLANE.md` — reconciliation, events and recovery authority
- `docs/CAPABILITY_DISCOVERY.md` — platform-neutral capability discovery/HAL
- `docs/EXECUTION_MODEL.md` — declarative environments and workload lifecycle
- `docs/NAMESPACE.md` — unified logical namespace
- `docs/DISTRIBUTED_FUTURE.md` — multi-node architecture direction
- `docs/RUNTIME.md` — minimal resident runtime
- `docs/SYSTEM_IN_SYSTEM.md` — host/guest/system-in-system model
- `src/fs_overlay/storage_engine.py` — local manifest/chunk/object/journal/inventory/Merkle/transaction foundation
- `src/fs_overlay/storage_resilience.py` — snapshots, recovery ordering, placement and quarantine
- `src/fs_overlay/carrier.py` — explicit carrier adapter boundary
- `src/fs_overlay/event_log.py` — structured append-only event records
- `src/fs_overlay/` — Python reference implementation
- `tests/` — existing reference tests
- `config.example.toml` — explicit-root configuration example

## Current implementation status

The local storage/resilience reference layer is implemented through transactional journal visibility, immutable snapshots, deterministic recovery planning, carrier placement scoring and quarantine evidence. Production AEAD, erasure coding, cross-platform adapters, isolation backends and distributed federation still require independently reviewed implementations and platform-specific validation.

This repository deliberately does not claim production durability, cryptographic certification, distributed transaction guarantees or successful recovery when the available evidence is insufficient.

## Non-goals

- stealth persistence;
- modification of arbitrary OS/system files;
- bypassing host access controls;
- unsafe mutation of unsupported file formats;
- treating a single metadata database as a recovery dependency;
- claiming kernel/hypervisor authority from ordinary user-space code.
