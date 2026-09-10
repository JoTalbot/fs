# Transaction-aware Execution

`TransactionExecutor` is the final gate between an admitted boundary plan and
a concrete process executor in the reference runtime.

```text
Boundary Plan
    |
    +-- admitted? -- no --> rejected
    |
   yes
    |
Prepare / invoke injected executor
    |
Observe ProcessResult
    |
Evidence Provider
    |
Verify required checks
    +-- fail --> Abort / verification_failed
    |
   pass
    |
Committed outcome
```

The executor is dependency-injected so the transaction layer cannot silently
select a privileged or host-mutating implementation. A concrete backend must
perform the actual namespace, filesystem, network, and resource setup before
starting the workload and must provide evidence for any claimed boundary.

Linux namespace probes can be adapted into verification evidence through
`probe_verification.linux_namespace_evidence`. The check identifiers use the
explicit `namespace:<mount|pid|net>` form. A successful namespace probe proves
only the namespace operation tested by that probe. It does not prove bind
mounts, root filesystem replacement, cgroup enforcement, or other stronger
semantics.

A failed or rejected transaction is never represented as committed state.
The reference layer provides an optional compensation hook, but it does not
pretend that arbitrary external side effects are automatically reversible.
