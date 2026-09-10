# Linux Network Namespace Boundary

FS represents network policy semantically. The backend may translate
`network=deny` into a Linux network namespace, but the presence of `unshare`
does not prove that the kernel will allow an unprivileged caller to create or
use the namespace.

Therefore:

```text
network policy
    -> backend capability
    -> namespace plan
    -> execution attempt
    -> observation
    -> verification
    -> commit only if verified
```

`network=host` is an explicit host-network policy and requires no network
namespace. Other policies are rejected unless a backend can actually enforce
them. No interface configuration, routing changes, firewall changes, or host
network policy mutation belongs in this plan-only layer.
