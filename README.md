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

Implemented primitives include versioned manifests, deterministic fixed-size chunking, SHA-256 content addressing, atomic temporary-file replacement, replayable journal-backed inventory, transaction begin/commit/abort visibility, Merkle roots, structured events, immutable snapshots, deterministic recovery graphs, failure-domain-aware carrier ranking, quarantine records, and semantic object/state primitives.

`StorageTransaction` stages immutable data and publishes metadata only after a durable transaction commit marker. Recovery ignores transactions without that marker.

The HMAC development envelope is **integrity-only** and is deliberately not presented as encryption. Production confidentiality requires an audited AEAD provider. Erasure coding likewise remains an explicit provider interface until an audited implementation is selected.

## Semantic state layer

`state_primitives.py` supplies dependency-free contracts for the next control-plane boundary:

- `ObjectContract` for desired/actual/health/generation state;
- `ProvenanceRecord` for attributable state history and evidence links;
- `DependencyGraph` with cycle rejection;
- expiring, revocable `Lease` objects with fencing tokens;
- confidence-bounded `KnowledgeRecord` objects;
- reproducible `DecisionRecord` objects tied to evidence and policy;
- immutable `WorldStateSnapshot` records;
- deterministic `reconcile()` and explicit `safe_stop()` results.

These structures do not grant authority. Execution still requires policy, admission, backend capability and observable verification.

## Resilience model

The storage layer distinguishes:

- **HEALTHY** — full configured redundancy is present;
- **DEGRADED** — enough shards remain for recovery, but redundancy is below target;
- **REPAIRING** — an approved repair is being executed;
- **UNRECOVERABLE** — fewer than the required data-shard threshold remains.

Snapshots contain object identities and a deterministic Merkle root rather than another copy of the data. Recovery dependencies are ordered explicitly by `RecoveryGraph`; cycles are rejected. Carrier selection consumes approved/healthy carrier facts and failure-domain information, while a plan itself never grants authority to mutate a carrier. Unexpected carrier changes are recorded in a quarantine ledger rather than silently overwritten.

See `docs/STORAGE_RESILIENCE.md` for the durability and recovery contract.

## Federation and minimal initiator

FS federation is a transport-neutral control-plane boundary. Nodes use explicit identity/trust admission, canonical signed envelopes, replay protection, durable acceptance state, deterministic reconciliation, verified replication and failure-domain-aware placement.

```text
local bootstrap
      |
      v
 identity + capabilities
      |
      v
 signed envelope
      |
      v
 explicit transport
      |
      v
 signature/freshness/replay/trust admission
      |
      v
 durable state -> policy -> reconciliation
      |
      v
 authorized execution -> verification -> audit
```

The reference `MinimalInitiator` requires explicit bootstrap configuration and injected key, signing and transport providers. It does **not** discover peers, open arbitrary sockets, select unauthorized carriers or modify the host. Capability negotiation fails closed on protocol-version mismatch. Key lifecycle state explicitly distinguishes active, retired and revoked keys. Versioned conformance vectors make canonical serialization independently testable.

The same core contract is designed to be embedded in a server, desktop, mobile, ARM or IoT launcher. Platform-specific networking, secure key storage and cryptography belong behind explicit adapters.

See `docs/FEDERATION_PROTOCOL.md` and `docs/FEDERATION_CONFORMANCE.md` for the protocol and production boundaries.

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
