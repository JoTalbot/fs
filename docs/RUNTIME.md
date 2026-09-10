# FS Runtime

## Goal

FS Runtime is intentionally small. Its job is to start, supervise and expose the FS storage engine; it is not the storage engine itself.

The runtime has four conceptual layers:

```text
                 fsd / fs-runtime
                       |
          +------------+------------+
          |                         |
   Storage Engine             Control API
          |                         |
   +------+-------+          status / repair
   |      |       |
 scanner carrier metadata

        Managed Workspace
              |
       normal application IO
```

## Managed workspaces

A workspace is an explicit, user-created root whose files are managed by FS. This gives the project the useful property that project/work files, caches, state, manifests, and generated artifacts can participate in the same storage policy without requiring an OS-wide hidden scan.

Example:

```toml
[[workspaces]]
name = "project"
root = "/srv/my-project"
mode = "managed"

[[workspaces]]
name = "data"
root = "/srv/my-data"
mode = "managed"
```

On Windows the equivalent roots use normal Windows paths. Paths are normalized through the platform adapter rather than hard-coded POSIX assumptions.

## Modes

### Managed

FS owns the workspace policy and can place FSOV envelopes into eligible files inside the workspace.

### Observed

FS records inventory, integrity and capacity but does not mutate host files. This is useful during migration and audit.

### Offline

FS engine works against an explicitly provided container or export without a resident daemon.

## Minimal daemon

The daemon should remain deliberately boring:

- load configuration
- open or lock the FS metadata state
- start the storage engine
- expose a small local control endpoint
- supervise audit/repair workers
- stop cleanly and flush state

It should not perform application-specific work, UI, arbitrary process injection, hidden persistence or system-wide discovery.

## Process model

```text
fs-runtime
  |
  +-- storage worker
  +-- audit worker
  +-- repair worker (on demand)
  +-- local control API
```

Where the platform supports it, the runtime can run as a native service. Otherwise it runs as a normal foreground process. Installation should never require a privileged service when the configured workspace can operate without one.

## Cross-platform abstraction

The core package must not depend on OS-specific APIs. Use adapters for:

- path semantics
- file locking
- atomic replace/rename
- fsync / flush
- filesystem identity
- service lifecycle
- process signal handling
- local IPC

Initial platform targets:

1. Linux
2. Windows
3. macOS
4. BSD/Unix-compatible systems where the adapter contract can be satisfied

## Adaptive behavior

Capabilities are detected at startup and cached in a runtime capability record:

```text
platform
filesystem
atomic_replace
file_locking
fsync_strength
service_manager
ipc_transport
path_case_sensitivity
max_component_length
```

The engine selects the safest supported implementation rather than assuming a Linux-like filesystem everywhere.

## Workspace lifecycle

```text
NEW
  -> DISCOVERED
  -> INITIALIZING
  -> HEALTHY
  -> DEGRADED
  -> REPAIRING
  -> HEALTHY
```

A workspace can be detached without destroying the virtual container. Detachment only removes its carrier role from placement decisions.

## Bootstrap principle

Keep the resident code small. Heavy functionality such as repair algorithms, format handlers and optional integrations should be loadable modules. The daemon's critical path should be sufficient to recover metadata and start the engine, not contain every feature in one executable.
