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
    +-- non-success --> failed
    |
   success
    |
Committed outcome
```

The executor is dependency-injected so the transaction layer cannot silently
select a privileged or host-mutating implementation. A concrete backend must
still perform the actual namespace, filesystem, network, and resource setup
before starting the workload and must provide evidence for any claimed
boundary.

A failed or rejected transaction is never represented as committed state.
The current reference layer does not implement rollback of external side
effects; that belongs to a future backend-specific compensation contract.
