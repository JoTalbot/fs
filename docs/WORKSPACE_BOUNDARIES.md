# FS Workspace Boundaries

FS treats a workspace as a managed logical object, not as an arbitrary host
path. A host path may be used for execution only after an explicit ownership
or delegation fact has been admitted by the control plane.

## Contract

`WorkspaceBinding` contains:

- stable FS workspace identity;
- host path used by a backend;
- explicit ownership/delegation admission;
- optional read-only intent.

`plan_workspace()` is observational and plan-only. It checks that the path is
absolute, exists, and is a directory, but it never treats existence as proof of
ownership.

## Security boundary

A workspace binding does not itself create a mount namespace or filesystem
root. Those are backend responsibilities. In particular, the current Linux
namespace backend must not claim `workspace-only` enforcement until it has a
verified mount-namespace implementation capable of exposing only the admitted
workspace.

Likewise, an FS workspace must never cause an unrelated host directory to be
mounted, deleted, permission-changed, or otherwise modified implicitly.

## Execution path

```text
FS Workspace Object
        |
        v
Ownership / Delegation Admission
        |
        v
WorkspaceBinding
        |
        v
WorkspacePlan
        |
        v
Backend-specific mount/root setup
        |
        v
Execution + Observation + Verification
```

The current implementation stops before the backend-specific mount/root step.
This is deliberate: claiming isolation before the kernel enforces it would
turn a security boundary into documentation theatre.
