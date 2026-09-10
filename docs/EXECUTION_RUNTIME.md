# FS Execution Runtime

The reference runtime has three explicit layers that must not be conflated:

1. **Admission**: the coordinator validates workspace ownership/delegation,
   backend availability, and resource lease authority.
2. **Execution**: concrete platform backends execute an already-admitted workload.
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

Admission declares `resource-controller` as a guarantee whenever a non-empty
budget is admitted with a valid lease. The transaction layer converts that
guarantee into the required `resource:enforcement` verification check. Only a
`ProcessSupervisor` execution result carrying `resource-controller-enforced`
satisfies that check. A valid lease by itself is therefore never treated as
proof that the native controller actually enforced the budget.

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

## Cross-platform backend boundary

### Windows

`WindowsJobObjectBackend` is a native Win32 adapter. It creates a per-execution
Job Object, applies CPU hard-cap, job-memory and active-process limits through
`SetInformationJobObject`, assigns the spawned process to that job, and queries
the limits back before reporting `verified=True`. The Job Object handle remains
owned by the backend until the supervisor releases it after process completion.
Unsupported disk limits and invalid budgets fail closed. Microsoft documents Job
Objects as the native mechanism for grouping processes and applying these
limits.

### macOS

There is deliberately no generic Python `sandbox-exec` fallback. Apple's App
Sandbox is kernel-enforced and entitlement/signing based, so a production FS
adapter must launch a signed helper/runtime carrying the required entitlements.
The current capability negotiation therefore reports macOS as requiring a
signed sandbox runtime rather than pretending that a normal child process has
been sandboxed.

### POSIX/BSD

Generic POSIX process execution is not advertised as an isolation backend. BSD
platforms require their own native capability adapters, such as Capsicum where
supported. Until the exact mechanism is configured and observed, capability
negotiation fails closed rather than mapping generic POSIX semantics to a
stronger security guarantee.

## Capability and backend contracts

`backend_capabilities.py` performs conservative platform negotiation and never
advertises a resource or isolation feature without a concrete backend contract.
`backend_contract.py` provides a versioned contract for backend identity,
evidence markers and supported resource types. Contract compatibility is
explicit and can be rejected when the runtime and backend versions differ.

These components are intentionally composable. The Linux and Windows resource
paths now have concrete native implementations and tests. macOS signed-runtime
and BSD native isolation remain explicit follow-on adapters, not hidden claims.
The repository also remains below the full production lifecycle, recovery and
federation scheduler roadmap.
