# FS Object Model

FS is not limited to files. The control plane treats every managed resource as a typed object with identity, lifecycle, policy, state, dependencies, and recovery metadata.

## Object types

| Object | Purpose |
|---|---|
| `File` | Logical file stored in a workspace or container |
| `Directory` | Namespace containing files and child objects |
| `Workspace` | Explicit user-managed project boundary |
| `Volume` | Logical storage capacity presented to an environment |
| `Container` | Portable FS storage container |
| `Process` | Managed executable instance |
| `Service` | Long-lived process with restart/health policy |
| `Environment` | Complete execution context |
| `Snapshot` | Immutable point-in-time state reference |
| `Device` | Abstract host/virtual device capability |
| `Network` | Abstract connectivity policy and endpoint set |
| `Package` | Installable runtime/application artifact |
| `Policy` | Declarative permissions/resource/security rules |

## Common object envelope

Every object has a stable UUID and a generation. Mutable state is represented as a new generation; recovery records retain the previous known-good generation.

```yaml
id: 01J...
type: workspace
name: example
schema: fs.object/v1
generation: 42
state: healthy
created_at: 2026-09-10T00:00:00Z
updated_at: 2026-09-10T00:00:03Z
labels:
  project: example
policy_ref: policy/example
snapshot_ref: snapshot/previous
```

## Relationships

Objects form a graph rather than a flat tree.

```text
Environment
 ├─ Workspace ── Volume ── Container
 ├─ Process ── Package
 ├─ Service ── Process
 ├─ Network
 ├─ Device
 ├─ Policy
 └─ Snapshot
```

This allows FS to answer questions such as:

- which files belong to a running environment;
- which process owns a changed file;
- which policy granted a capability;
- which snapshot can restore an environment;
- which host resources are required to recreate it.

## Lifecycle

Generic lifecycle states:

`NEW -> PROVISIONING -> READY -> RUNNING -> DEGRADED -> RECOVERING -> READY`

Terminal administrative states are `STOPPED`, `DETACHED`, and `QUARANTINED`.

Objects must not silently jump across lifecycle states. The control plane records transitions as events.

## Desired properties

1. **Addressable** - every managed object has a stable identifier.
2. **Declarative** - desired state can be represented as data.
3. **Observable** - current state and health can be queried.
4. **Recoverable** - important state points to a known-good generation.
5. **Policy-bound** - actions require an applicable policy.
6. **Platform-neutral** - the object model does not expose host-specific APIs.
7. **Auditable** - changes generate structured events.

## Object graph versus host graph

FS maintains a logical graph and maps it onto the host. The mapping is intentionally reversible:

```text
FS object graph
      |
      v
platform adapter
      |
      v
host resources
```

Deleting or detaching an FS object must not implicitly delete unrelated host resources.

## Environment as the top-level unit

An `Environment` is the main unit of orchestration. It can represent:

- a native application workspace;
- a sandboxed application;
- a containerized workload;
- a VM guest;
- eventually a complete FS-native operating environment.

The same declarative definition can therefore move between backends when capability discovery confirms compatibility.
