# FS System-in-System Architecture

## Vision

FS evolves from a storage overlay into a **portable execution environment**: a controlled system layer that owns a managed workspace, persistent state, policy, recovery and optional execution services while the host OS remains fully functional.

The key distinction is architectural: FS should not attempt to secretly replace the host OS. It should provide a stronger control plane *above* the host OS, and where the platform permits it, use supported virtualization, sandboxing, filesystem, service and security primitives to isolate workloads.

## Layer model

```text
+-------------------------------------------------------------+
| FS Control Plane                                            |
| policy | identity | storage | snapshots | recovery | IPC   |
+-------------------------------------------------------------+
| FS Runtime                                                  |
| process supervisor | workspace | package/runtime adapters  |
+-------------------------------------------------------------+
| Isolation Backend                                           |
| containers / namespaces / sandbox / VM / job objects       |
+-------------------------------------------------------------+
| Host OS                                                     |
| Windows | Linux | macOS | BSD | other supported systems   |
+-------------------------------------------------------------+
| Hardware / firmware                                         |
+-------------------------------------------------------------+
```

FS has two operating modes:

### Overlay mode

FS runs as a normal user-space service/daemon and manages storage, workspaces, processes and recovery using host-supported APIs.

### Root/isolation mode

Where stronger isolation is required, FS launches workloads inside a platform-supported sandbox, container, microVM or VM. The exact mechanism is selected by the platform adapter.

This makes the system portable without pretending that a normal user-space daemon can magically become a hypervisor.

## Host transparency

The host remains usable. Existing applications continue to run normally unless the operator explicitly places them inside an FS-managed workspace or isolation domain.

FS must never depend on intercepting every host process or modifying kernel behavior merely to provide its core storage features.

## FS-managed workspace

A workspace is a portable logical environment containing:

- source/work files
- configuration
- application state
- caches
- logs
- generated artifacts
- package/runtime metadata
- snapshots
- recovery metadata

A workspace can be exported/imported and reconstructed on another supported host subject to platform compatibility.

## Execution model

An FS workload is described declaratively:

```yaml
name: example
workspace: example-workspace
runtime: native
permissions:
  filesystem: workspace-only
  network: deny
resources:
  cpu: auto
  memory: auto
recovery:
  restart: on-failure
```

The supervisor translates this intent into the platform's native isolation primitive.

## Platform adapters

The core API is platform-neutral. Adapters implement:

- process creation and supervision
- filesystem operations
- file locking
- IPC
- service installation
- sandbox/isolation
- resource limits
- credentials
- signals/events
- startup/shutdown

Initial targets:

1. Linux: namespaces/cgroups/systemd where available; optional microVM backend.
2. Windows: Windows services, Job Objects and supported sandbox/virtualization APIs.
3. macOS: launchd and supported sandbox/process facilities.
4. Other Unix-like systems: POSIX baseline with capability detection.

## Minimal daemon principle

The resident component should contain only what must remain alive:

```text
fsd
 ├── health/watchdog
 ├── IPC endpoint
 ├── state coordinator
 └── worker launcher
```

Heavy work is event-driven or delegated to short-lived workers. The daemon should be restartable without corrupting the workspace.

## Super-system principle

The phrase "above the host OS" is treated as a **control-plane goal**, not a claim that user-space software can supersede a kernel. To obtain stronger authority, FS must use explicit, supported mechanisms such as a VM/hypervisor or privileged host integration.

The long-term architecture can therefore evolve to:

```text
Hardware
   ↓
Hypervisor / boot environment (optional)
   ↓
FS Control Plane
   ├── virtual storage
   ├── workspace manager
   ├── execution manager
   ├── policy engine
   └── recovery manager
          ↓
     Host OS VM / sandbox
          ↓
       Applications
```

This preserves a clean migration path from a normal application to a deeply integrated platform without making unsafe kernel-level modifications part of the initial product.

## Recovery guarantee

FS must guarantee only what it can verify. A host OS failure is not automatically recoverable by a user-space FS daemon. A VM-backed mode can provide stronger guarantees by moving the guest OS under FS control and storing its virtual disks in the FS container.
