# FS Isolation Backends

FS treats isolation as an explicit backend capability, never as an implicit side effect of execution.

## Contract

```text
Semantic Operation
    -> policy / authority validation
    -> resource admission
    -> backend selection
    -> isolation plan
    -> execution
    -> observation
    -> verification
```

An isolation backend must declare what it can actually provide. Platform labels are not sufficient evidence of a guarantee.

## Linux

The reference `LinuxNamespaceBackend` can discover the host `unshare` utility and construct an explicit namespace launch prefix using mount and PID namespaces. The backend does not call privilege escalation and does not change kernel policy.

An available `unshare` binary therefore means **possible**, not **guaranteed**. Kernel configuration, user namespaces, security policy and container restrictions can still reject the operation. Execution must report the resulting observation rather than claiming isolation merely because the command was constructed.

Resource limits through cgroups remain a separate concern. They require explicit resource admission and a platform-specific controller implementation.

## Windows

`WindowsJobObjectBackend` identifies Windows Job Objects as the intended isolation primitive but deliberately reports the binding as unavailable until a native implementation exists. The reference layer must never claim a Windows isolation guarantee that it cannot enforce and verify.

## Selection rules

- isolation is opt-in;
- discovery does not grant permission;
- capability does not imply authority;
- unsupported isolation fails closed;
- no backend may elevate privileges automatically;
- host functionality remains intact unless an operator explicitly selects an isolated deployment;
- backend claims must correspond to observable semantics;
- FS-IR remains backend-neutral and is lowered only after admission.

## Next implementation stages

1. Linux namespace execution adapter with explicit workspace and network policy boundaries.
2. Linux cgroup resource controller with lease/fencing semantics.
3. Windows Job Object execution adapter with resource limits.
4. FS-IR lowering into backend-specific execution plans.
5. Cross-platform semantic verification and conformance tests.
