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
different isolation mechanism. Bubblewrap 0.12.0 is required because older
releases are affected by a sandbox-setup symlink traversal vulnerability.

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

Admission now declares `resource-controller` as a guarantee whenever a
non-empty budget is admitted with a valid lease. The transaction layer converts
that guarantee into the required `resource:enforcement` verification check.
Only a `ProcessSupervisor` execution result carrying
`resource-controller-enforced` satisfies that check. A valid lease by itself is
therefore never treated as proof that the native controller actually enforced
the budget.

The current cgroup attachment occurs immediately after process creation. The
runtime reports enforcement only after controller writes and readback succeed;
it does not claim that a budget was enforced before the child existed.

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

The supervisor also carries the exact resource lease identity in
`ProcessResult` when resource enforcement succeeds, allowing later runtime
layers to correlate the observation with the admitted lease.

## Platform boundary

The Linux implementation is the first concrete isolation/runtime adapter. The
long-term roadmap still requires Windows Job Objects, a macOS service/runtime
adapter, POSIX/BSD baselines, capability negotiation and a versioned backend
contract. macOS's general-purpose `sandbox-exec` interface is deprecated and
undocumented for third-party custom sandbox profiles, so it must not be adopted
as an unverified substitute for the Linux boundary.

These components are intentionally composable. They do not yet constitute the
full cross-platform supervisor, lifecycle API, recovery system, or federation
scheduler described by the long-term roadmap.
