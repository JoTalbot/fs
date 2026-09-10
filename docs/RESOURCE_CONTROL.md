# FS Resource Control Boundary

FS treats resource limits as authority-bearing operations, not as metadata.
A declaration such as `memory_bytes` expresses a requirement; it does not
prove that the host will enforce it.

## Admission model

```text
ResourceBudget
    -> ResourceLease
    -> delegated/owned scope
    -> native controller
    -> enforcement
    -> observation
    -> verification
```

The lease identifies who may consume a bounded resource scope. A lease is not
a health guarantee and does not grant unrelated host privileges.

## Current implementation

`src/fs_overlay/resource_control.py` provides `ResourceLease` and
`ResourcePlan`. It is deliberately **plan-only**. A requested budget without a
valid active lease fails closed. Even with a valid lease, the current reference
runtime reports the plan as non-enforceable until a native resource controller
is attached.

The module does not write to `/sys/fs/cgroup`, create host-wide cgroups, change
limits of unrelated processes, or acquire privileges.

## Next enforcement step

A Linux cgroup adapter may be added only around an explicitly FS-owned or
operator-delegated subtree. It must validate controller availability, establish
ownership, apply limits before process admission, fence stale leases, observe
actual controller state, and verify the resulting process placement and limits.

Until those conditions exist, FS must report resource limits as requested but
not enforced. Human software has enough ways to lie about reality already.
