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
 NamespaceProbeResult
        ↓
 verification evidence
```

A successful probe does not prove workspace bind-mount isolation, root
filesystem replacement, cgroup enforcement, or any other guarantee that was
not directly tested. Conversely, a rejected probe must prevent the FS runtime
from claiming that namespace creation is available for that environment.

This deliberately avoids privileged setup, host-wide mutation, and persistent
changes. The next backend stage can build stronger probes for the exact
workspace and resource semantics it intends to enforce.
