# Capability Discovery and HAL

FS must adapt to a machine by discovering capabilities, not by treating an operating-system name as a capability matrix.

## Capability record

A platform adapter reports a normalized record:

```yaml
schema: fs.capabilities/v1
platform: linux
architecture: x86_64
filesystem:
  type: ext4
  case_sensitive: true
  max_component_length: 255
storage:
  atomic_replace: true
  file_locking: true
  durable_flush: true
execution:
  process_control: true
  job_control: false
  namespaces: true
  cgroups: true
  container_runtime: true
  vm_backend: true
  vm_backend_name: qemu
services:
  manager: systemd
ipc:
  unix_socket: true
  named_pipe: false
security:
  secure_key_store: available
resources:
  cpu_count: 16
  memory_bytes: 34359738368
  acceleration: kvm
```

Values are discovered at runtime and must distinguish `true`, `false`, `unknown`, and `restricted` rather than forcing everything into booleans.

## HAL responsibilities

The Hardware/Host Abstraction Layer exposes narrow interfaces for:

- filesystem operations;
- durable writes and flushes;
- file locking;
- process lifecycle;
- service lifecycle;
- local IPC;
- resource accounting;
- sandbox/isolation;
- virtualization;
- credentials and secret-provider references;
- clock and monotonic timing;
- signals and shutdown notifications.

No core module should import platform-specific process, service, or virtualization APIs directly.

## Backend selection

Environment definitions can use:

```yaml
runtime: auto
```

The planner ranks available backends:

```text
native
  -> sandbox/container
  -> microVM/VM
```

Selection is constrained by declared policy. A workload that requires a Linux kernel feature must not be silently moved to a backend that cannot provide it.

The planner should return an explanation record:

```yaml
selected: container
candidates:
  - backend: native
    eligible: false
    reasons: [filesystem_isolation_required]
  - backend: container
    eligible: true
  - backend: vm
    eligible: true
    score: 0.71
```

## Capability probing rules

Probing must be:

1. read-only by default;
2. bounded in time;
3. cached with a capability-version and timestamp;
4. reproducible for diagnostics;
5. invalidated when relevant host configuration changes.

A failed probe means `unknown`, not permission to guess.

## Cross-platform strategy

Initial adapters target Linux, Windows, macOS, and generic Unix/BSD. They share the same object/control-plane interfaces while mapping to native primitives.

The abstraction must describe semantics rather than APIs. For example, the core asks for `durable_flush(path)`, while the adapter chooses the correct host mechanism.

## Future boot-level backend

A future boot/hypervisor implementation can expose stronger primitives such as:

- virtual machine creation;
- virtual disk attachment;
- virtual network creation;
- hardware partitioning;
- guest lifecycle;
- measured boot and attestation.

This backend is additive. The ordinary user-space FS runtime remains usable on systems without it.
