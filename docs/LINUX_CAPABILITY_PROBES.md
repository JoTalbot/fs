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
stronger disposable probe. When the explicitly installed `bubblewrap` backend
is available, it creates a temporary workspace containing a sentinel, exposes
that workspace at `/workspace`, and verifies from inside the sandbox that the
workspace sentinel is visible while an unbound host-root path is absent.

Bubblewrap is used as an explicit backend, not as an implicit privilege
escalation or user-namespace fallback. If the backend is unavailable or the
kernel rejects its setup, the probe fails closed. Bubblewrap's documented
model creates a new filesystem namespace and can bind selected host paths
into it.

This probe is evidence for the exact property it tests. It does not by itself
prove device isolation, cgroup enforcement, resource limits, or a stronger
security boundary than the tested filesystem visibility. It is also not yet
wired to the `workspace-binding-admitted` guarantee; that mapping must wait
until the concrete execution backend actually uses the same boundary and
passes this evidence through the transaction gate.

All probes avoid persistent host changes. Unknown or unavailable guarantees
remain fail-closed.
