# Execution Boundary Coordinator

`execution_coordinator.py` combines the independent admission layers into one
fail-closed decision before execution.

```text
EnvironmentSpec
    |
    +--> Workspace admission / mount boundary
    |
    +--> Network namespace admission
    |
    +--> Resource lease admission
    |
    `--> ExecutionBoundaryPlan
             |
             +--> admitted
             +--> reasons
             `--> backend-specific execution
```

The coordinator is deliberately plan-only. It does not start processes,
create namespaces, mount paths, or write cgroup configuration.

An environment using `workspace-only` requires an explicitly admitted
`WorkspaceBinding`. Network and resource requirements are independently
validated. Any unmet requirement blocks admission rather than silently
weakening the requested policy.

The next enforcement stage is a transaction-aware Linux executor that consumes
this plan, establishes every required boundary before process start, observes
the resulting sandbox, and verifies the declared guarantees before committing
the execution state.
