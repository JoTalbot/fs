# Linux Mount Namespace Boundary

FS treats a workspace as a logical object. A host path becomes usable by an
execution backend only after an explicit `WorkspaceBinding` records ownership
or delegation.

`mount_namespace.py` currently provides a **plan-only** Linux boundary:

```text
FS Workspace
    -> admitted WorkspaceBinding
    -> mount namespace plan
    -> future mount/root setup helper
    -> process execution
    -> observation + verification
```

The plan may report the Linux `unshare` mechanism and namespace guarantees, but
it does not perform mounts, change the host mount table, change permissions, or
create a filesystem root. Availability of `unshare` is not proof that the
kernel will permit an unprivileged namespace operation.

## Required enforcement before `workspace-only` is advertised

A production backend must construct the mount namespace and establish the
workspace boundary before starting the workload. It must also verify that the
resulting process cannot access paths outside the admitted workspace according
to the declared policy. Failure to establish or verify that boundary must fail
closed.

Read-only workspaces must be enforced by the mount configuration, not merely
recorded in metadata.
