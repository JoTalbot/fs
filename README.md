# FS — Portable System Substrate

FS starts as a user-controlled, failure-tolerant storage overlay and is designed to grow into a portable system control plane.

The long-term goal is not merely to hide more bytes inside files. It is to make **storage, workspaces, processes, services, environments, isolation, snapshots, policy and recovery parts of one coherent system model**.

> **Safety boundary:** FS never silently scans or modifies the whole operating system. Carrier roots and managed workspaces are explicitly configured, protected/system paths are denied, and mutations are attributable and auditable.

## Storage foundation

```text
container data
    -> compress (optional)
    -> encrypt/authenticate
    -> chunk
    -> erasure-code
    -> place shards into approved carriers
    -> verify

carrier loss/corruption
    -> audit
    -> reconstruct
    -> choose approved replacement
    -> repair redundancy
```

FS uses erasure coding rather than relying on identical copies. The configured `data_shards` / `parity_shards` policy determines how many carrier failures can be tolerated.

The 30% carrier rule is a **hard maximum overhead**, not a target:

```text
usable_capacity = min(file_size * 0.30, configured_limit, format_safe_limit)
```

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
- `src/fs_overlay/` — Python reference implementation scaffold
- `tests/` — reference tests
- `config.example.toml` — explicit-root configuration example

## Current implementation status

The repository currently contains a safe reference architecture plus the first dependency-free control-plane models and capability-aware backend planner.

The next engineering milestone is the local storage engine: manifests, deterministic chunking, authenticated-encryption interfaces, erasure-coding interfaces, carrier adapters, atomic append/recovery journal, redundant inventory metadata, and audit/recovery commands.

Production cryptography, erasure coding, cross-platform adapters and isolation backends must be independently tested and security-reviewed before production data or privileged workloads are entrusted to FS.

## Non-goals

- stealth persistence;
- modification of arbitrary OS/system files;
- bypassing host access controls;
- unsafe mutation of unsupported file formats;
- treating a single metadata database as a recovery dependency;
- claiming kernel/hypervisor authority from ordinary user-space code.
