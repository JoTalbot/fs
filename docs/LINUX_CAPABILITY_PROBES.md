# Linux Capability Probes

FS treats backend availability and actual enforcement as separate facts.

`fs_overlay.linux_probe.probe_namespace()` performs a bounded, disposable
runtime probe for the requested Linux namespace. It currently probes mount,
pid, and network namespaces through `unshare`.

The probe result is observational evidence:

```text
namespace + runtime
        ↓
 disposable probe
        ↓
 actual kernel result
        ↓
 namespace identity observed
        ↓
 NamespaceProbeResult
        ↓
 verification evidence
```

The probe records the namespace identity visible to the child and compares it
with the caller's `/proc/self/ns/<type>` identity. A zero exit code alone is
not enough: the namespace must actually be observed as different. For PID
namespaces the disposable child is created with `unshare --fork`, because the
calling process itself is not moved into a new PID namespace by `unshare(2)`.

## Workspace boundary evidence

`fs_overlay.workspace_boundary.probe_workspace_boundary()` is a separate,
disposable capability probe. When the explicitly installed `bubblewrap`
backend is available, it creates a temporary workspace containing a sentinel,
exposes that workspace at `/workspace`, and verifies from inside the sandbox
that the workspace sentinel is visible while an unbound host-root path is
absent.

The concrete `BubblewrapWorkspaceBackend` is the execution path used for an
admitted `workspace-only` workload. The actual workload is wrapped with the
same boundary checks before and after execution, so the transaction verifier
can distinguish execution-scoped evidence from a separate disposable probe.
The result records the backend identity and exact observation markers.

For `network=deny`, the concrete Bubblewrap execution additionally compares
the sandbox `/proc/self/ns/net` identity with the parent's network namespace
identity before and after the workload. A successful exit without this
observation is not accepted as network-isolation evidence. `network=host`
does not emit a network-isolation marker.

Workspace write semantics are explicit: a read-only workspace uses
`--ro-bind`, while a writable admitted workspace uses `--bind`. The evidence
still proves only the declared workspace visibility boundary, not arbitrary
content integrity or resource isolation.

Bubblewrap is used as an explicit backend, not as an implicit privilege
escalation or fallback. The backend requires Bubblewrap >= 0.12.0 because
versions before 0.12.0 have a published sandbox-setup symlink traversal
vulnerability. If the backend is unavailable or setup fails, admission fails
closed.

These probes and execution checks do not prove device isolation, cgroup
enforcement, resource limits, or a stronger security boundary than the tested
property. `workspace-binding-admitted` remains an admission fact rather than
runtime evidence. Unknown or unavailable guarantees remain fail-closed.

All disposable probes avoid persistent host changes.
