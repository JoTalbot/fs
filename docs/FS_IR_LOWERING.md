# FS-IR Backend Lowering

FS-IR describes intent and execution semantics without binding them to a host API. Backend lowering is the controlled translation step between the semantic model and an admitted execution backend.

```text
FS-IR
  -> policy / authority validation
  -> capability match
  -> backend selection
  -> backend lowering
  -> admitted execution
  -> observation
  -> verification
```

## Rules

1. Lowering never grants authority.
2. Lowering never weakens a requested policy silently.
3. Unsupported semantics fail closed.
4. Native execution is eligible only for explicitly host-visible filesystem/network policy and constraints it can enforce.
5. Workspace-only filesystem, denied/isolated network, device access and resource limits require a backend that actually enforces those semantics.
6. Linux namespaces are currently represented as an explicit launch plan only. `unshare` availability does not prove that the kernel will permit the operation.
7. Windows Job Object lowering remains unavailable until a native binding exists.
8. A lowered plan is data, not proof that execution succeeded. Verification follows execution.

## Current reference boundary

`src/fs_overlay/lowering.py` produces a `LoweredExecution` containing backend name, argv, environment and declared guarantees. It does not start processes.

The Linux namespace backend currently exposes mount/PID namespace launch semantics. Filesystem and network policy remain rejected there until their enforcement boundaries are implemented.

This separation keeps the architecture honest: the planner chooses what is feasible, the lowering layer translates it, the backend executes it, and the observation/verification layer decides what actually happened.
