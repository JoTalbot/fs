# FS Execution Runtime

The reference runtime now has three explicit layers that must not be conflated:

1. **Admission**: the coordinator validates workspace ownership/delegation,
   backend availability, and resource lease authority.
2. **Execution**: concrete Linux backends execute an already-admitted workload.
3. **Observation/verification**: the transaction layer accepts only evidence
   produced by the exact execution that created the declared boundary.

## Workspace and network

`BubblewrapWorkspaceBackend` is the explicit Linux workspace backend. It
requires Bubblewrap >= 0.12.0, preserves read-only/read-write workspace policy,
and can request host or denied networking. For denied networking, the actual
sandbox compares its `/proc/self/ns/net` identity with the parent's identity.

The backend never silently falls back to privileged namespace creation or a
different isolation mechanism.

## Resource control

`LinuxCgroupV2Backend` accepts only an active `ResourceLease` whose scope is an
existing absolute cgroup v2 directory. It does not create host-wide cgroups.
It supports CPU, memory and PID limits through their native cgroup v2 control
files and fails closed for unsupported disk limits or missing/non-writable
controllers. After writing limits it reads the exact values back before
reporting `verified=True`.

The resource scope is treated as delegated authority, not discovered authority.
The backend rejects symlink scopes so the lease cannot silently redirect the
write target during scope resolution.

## Process supervision

`ProcessSupervisor` owns a bounded `Popen` lifecycle. It uses argv directly,
never a shell, captures output with `communicate()`, terminates timed-out
children and escalates to kill when required. On POSIX it starts a new session
and terminates the process group, so a timed-out workload does not remain as a
stray child by default.

Restart is explicitly bounded by `max_restarts` and only applies to failures,
not timeouts. If a requested resource budget cannot be enforced inside its
explicit lease, the supervisor terminates the child and returns failure rather
than running without the requested resource boundary.

These components are intentionally composable. They do not yet constitute the
full cross-platform supervisor, lifecycle API, recovery system, or federation
scheduler described by the long-term roadmap.
