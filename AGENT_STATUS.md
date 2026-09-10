# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `ff35888c475287d288481144c3347aa14ca6af6f`
- Updated: 2026-09-10

## Current architectural phase

**Evidence-backed execution boundaries + concrete backend semantics**

FS is moving from descriptive execution planning toward a verified execution loop. Linux namespace capability probes are explicit runtime evidence, boundary guarantees deterministically become required verification checks, and concrete backends must emit execution-scoped evidence for the exact semantics they claim.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | concrete workspace/network execution evidence + backend semantics | `src/fs_overlay/isolation.py`, `src/fs_overlay/linux_executor.py`, `src/fs_overlay/execution_coordinator.py`, `src/fs_overlay/evidence_provider.py`, `src/fs_overlay/verification_requirements.py`, tests/docs/status/log | `ff35888c475287d288481144c3347aa14ca6af6f` | active | Preserve read/write semantics, make Bubblewrap network evidence execution-scoped, then validate full CI and record the result |

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

### Execution-scoped workspace evidence

- `ProcessResult` carries backend identity and execution evidence.
- Bubblewrap wraps the actual workload with boundary checks performed before and after that workload in the same sandbox.
- The evidence provider accepts `workspace:boundary` only when the result came from `bubblewrap-workspace` and carries the exact observed marker.
- Reserved boundary-observation failures fail the execution closed.
- The generic disposable workspace probe remains separate and is not used as evidence for another execution.

### Guarantee-to-check mapping

- `workspace-filesystem-boundary` maps to required `workspace:boundary` evidence.
- `workspace-binding-admitted` remains distinct from runtime observation. Ownership/delegation is an admission fact; it is not runtime evidence.
- Namespace guarantees continue to use their existing namespace evidence provider until an exact backend-specific execution evidence path replaces them.

## Validation state

- CI run `34438094451` (run #22): PASS, Python 3.11/3.12/3.13.
- CI run #40 `34443788344`: PASS, workspace admission.
- CI run #41 `34443796582`: PASS, execution-scoped workspace evidence.
- CI run #42 `34443820903`: PASS, Python 3.11/3.12/3.13; all three matrix jobs completed successfully.
- The next change must add no stronger guarantee without a matching execution-scoped evidence path.

## Known non-goals for this phase

- Do not implement privileged namespace creation.
- Do not assume `unshare` proves workspace isolation.
- Do not silently introduce user namespaces as a fallback.
- Do not mutate host-wide cgroups.
- Do not claim resource enforcement without an enforceable FS-owned/delegated resource lease.
- Do not turn FS-IR directly into host mutation without authority, admission, execution, observation, verification, and transaction gates.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
