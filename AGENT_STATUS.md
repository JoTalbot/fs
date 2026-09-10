# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `6ae5d21bb6dfc46e0cf376b1e186881659b31a9a`
- Updated: 2026-09-10

## Current architectural phase

**Evidence-backed execution boundaries + concrete backend semantics**

FS is moving from descriptive execution planning toward a verified execution loop. Linux namespace capability probes are explicit runtime evidence, boundary guarantees deterministically become required verification checks, and concrete backends must emit execution-scoped evidence for the exact semantics they claim.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | execution-boundary completion | workspace/network backend, executor, evidence provider, coordinator, tests/docs | `ff35888c475287d288481144c3347aa14ca6af6f` | completed and CI green | Start the next roadmap implementation only after fresh repository/security research: concrete delegated resource-controller backend, then supervisor/lifecycle integration |

## Recently completed

### Namespace identity verification

- `probe_namespace()` executes a disposable namespace child and observes `/proc/self/ns/<type>` inside it.
- A successful `unshare` exit is insufficient if the child reports the same namespace identity as the parent.
- PID probes use `--fork` so the observed child is actually inside the new PID namespace.

### Concrete workspace backend

- `BubblewrapWorkspaceBackend` is an explicit Linux backend requiring bubblewrap >= 0.12.0.
- The workspace path must be absolute, existing, a directory, and must not overlap the runtime paths exposed read-only by the backend.
- The backend preserves explicit `network=host` versus `network=deny` semantics and never silently enables a fallback mechanism.
- Workspace-only admission now requires the concrete backend instead of merely seeing `unshare`.
- Workspace read/write policy is preserved: read-only uses `--ro-bind`, writable uses `--bind`.

### Execution-scoped workspace/network evidence

- `ProcessResult` carries backend identity and execution evidence.
- Bubblewrap wraps the actual workload with filesystem boundary checks performed before and after that workload in the same sandbox.
- For `network=deny`, the same wrapper compares the sandbox `/proc/self/ns/net` identity with the parent network namespace identity before and after the workload.
- The evidence provider accepts workspace/network evidence only from the exact Bubblewrap execution result and exact markers.
- Reserved boundary-observation failures fail the execution closed.
- The generic disposable probes remain separate and are not used as evidence for another execution.

### Guarantee-to-check mapping

- `workspace-filesystem-boundary` maps to required `workspace:boundary` evidence.
- `network-namespace` continues to map to `namespace:net`, but a Bubblewrap execution satisfies that check only through its exact execution-scoped network marker.
- `workspace-binding-admitted` remains distinct from runtime observation. Ownership/delegation is an admission fact; it is not runtime evidence.

## Validation state

- CI run `34438094451` (run #22): PASS, Python 3.11/3.12/3.13.
- CI run #40 `34443788344`: PASS, workspace admission.
- CI run #41 `34443796582`: PASS, execution-scoped workspace evidence.
- CI run #42 `34443820903`: PASS, Python 3.11/3.12/3.13.
- CI run #56 `34444479095`: PASS, Python 3.11/3.12/3.13, after fixing the first failing test batch.
- Current latest commit `6ae5d21bb6dfc46e0cf376b1e186881659b31a9a` is the green validated head.

## Known non-goals for this phase

- Do not implement privileged namespace creation.
- Do not assume `unshare` proves workspace isolation.
- Do not silently introduce user namespaces as a fallback.
- Do not mutate host-wide cgroups.
- Do not claim resource enforcement without an enforceable FS-owned/delegated resource lease.
- Do not turn FS-IR directly into host mutation without authority, admission, execution, observation, verification, and transaction gates.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
