# FS Execution Model

FS treats execution as a resource graph derived from declarations. A workload is not a shell command wrapped in a supervisor; it is a desired environment state.

## Workload declaration

```yaml
apiVersion: fs/v1
kind: Environment
metadata:
  name: example
spec:
  workspace: example-workspace
  runtime: auto
  command: ["python", "-m", "app"]
  policy:
    filesystem: workspace-only
    network: deny
    devices: []
  resources:
    cpu_millis: 2000
    memory_bytes: 1073741824
    disk_bytes: 5368709120
  recovery:
    restart: on-failure
    max_restarts: 5
```

The declaration is data. The controller turns it into objects and operations.

## Execution graph

```text
Environment
   |
   +-- Workspace
   +-- Volume
   +-- Policy
   +-- Network
   +-- Devices
   +-- Process(s)
   +-- Service(s)
   +-- Snapshot(s)
```

Dependencies are explicit. A process cannot start before its workspace and required policy have reached `READY`.

## Reconciliation loop

```text
observe -> compare -> plan -> authorize -> execute -> verify -> publish
   ^                                               |
   +-----------------------------------------------+
```

A crash between execute and publish is resolved from idempotency records and postcondition checks.

## Restart policy

The initial policy vocabulary:

- `never`
- `on-failure`
- `always`

Restart limits prevent endless crash loops. Backoff state is persisted so a control-plane restart does not reset the safety limit.

## Resource governance

Resource requirements are expressed portably. Adapters translate them to native mechanisms when available.

The scheduler must distinguish:

- hard limits: execution cannot exceed them;
- reservations: resources expected to be available;
- soft preferences: used for placement but not required.

Unknown enforcement support must not be reported as enforced.

## Process identity

A managed process has an FS object ID independent of its host PID. Host PIDs are observations and may change after restart.

This prevents a stale PID from being treated as the same logical process.

## Environment migration

A portable environment consists of:

- declarative specification;
- content-addressed workspace state;
- package/runtime references;
- required capability set;
- policy;
- snapshot/recovery references.

Host-specific process identifiers, socket paths and temporary directories are not portable state.

Migration procedure:

1. snapshot the source environment;
2. resolve target capabilities;
3. build a backend plan;
4. transfer required state;
5. validate policy compatibility;
6. instantiate target resources;
7. verify health;
8. switch ownership/reference state;
9. retain source snapshot for rollback.

## Long-term execution levels

FS can progressively support:

```text
L0  storage overlay
L1  managed native processes
L2  sandbox/container workloads
L3  microVM workloads
L4  full VM environments
L5  FS-native environments and boot integration
```

Higher levels add isolation and portability. They do not invalidate lower levels.
