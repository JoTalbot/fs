# FS — Portable System Substrate

FS starts as a user-controlled, failure-tolerant storage overlay and is designed to grow into a portable system control plane.

The long-term goal is not merely to hide more bytes inside files. It is to make **storage, workspaces, processes, services, environments, isolation, snapshots, policy and recovery parts of one coherent system model**.

> **Safety boundary:** FS never silently scans or modifies the whole operating system. Carrier roots and managed workspaces are explicitly configured, protected/system paths are denied, and mutations are attributable and auditable.

## Storage foundation

The local reference engine now provides the first concrete storage spine:

```text
input
  -> deterministic chunks
  -> content-addressed chunk objects
  -> immutable manifest
  -> fsync journal commit
  -> inventory
  -> audit / recovery
```

The storage engine includes versioned manifests, deterministic fixed-size chunking, SHA-256 content addressing, atomic temporary-file replacement, an append-only length-prefixed journal, replayable inventory, Merkle-DAG root primitives, an explicit authenticated-encryption provider boundary, an explicit erasure-coding provider boundary, and an explicit carrier adapter boundary.

The HMAC development envelope is **integrity-only** and is deliberately not presented as encryption. Production confidentiality requires an audited AEAD provider. Erasure coding likewise remains an explicit provider interface until an audited implementation is selected.

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
```

Storage commands operate only on the explicitly supplied storage root.

## Repository layout

- `docs/ARCHITECTURE.md` — normative storage architecture and invariants
- `docs/FORMAT.md` — FSOV carrier and manifest format
- `docs/OBJECT_MODEL.md` — unified managed-object model
- `docs/CONTROL_PLANE.md` — reconciliation, events and recovery authority
- `docs/CAPABILITY_DISCOVERY.md` — platform-neutral capability discovery/HAL
- `docs/EXECUTION_MODEL.md` — declarative environments and workload lifecycle
- `docs/NAMESPACE.md` — unified logical namespace
- `docs/DISTRIBUTED_FUTURE.md` — multi-node architecture direction
- `docs/RUNTIME.md` — minimal resident runtime
- `docs/SYSTEM_IN_SYSTEM.md` — host/guest/system-in-system model
- `src/fs_overlay/storage_engine.py` — local manifest/chunk/object/journal/inventory/Merkle foundation
- `src/fs_overlay/carrier.py` — explicit carrier adapter boundary
- `src/fs_overlay/event_log.py` — structured append-only event records
- `src/fs_overlay/` — Python reference implementation
- `tests/` — existing reference tests
- `config.example.toml` — explicit-root configuration example

## Current implementation status

The repository now has a concrete local storage spine in addition to the control-plane and execution reference layers. The next storage/resilience work is to integrate audited AEAD, an audited erasure-coding implementation, richer recovery semantics, carrier placement, snapshots and transactional state reconciliation.

Production cryptography, erasure coding, cross-platform adapters and isolation backends must be independently tested and security-reviewed before production data or privileged workloads are entrusted to FS.

## Non-goals

- stealth persistence;
- modification of arbitrary OS/system files;
- bypassing host access controls;
- unsafe mutation of unsupported file formats;
- treating a single metadata database as a recovery dependency;
- claiming kernel/hypervisor authority from ordinary user-space code.
