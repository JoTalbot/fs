# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `582efcc4f57da9f39f30a4eb88488e71bc924b3e`
- Updated: 2026-09-10

## Current architectural phase

**Evidence-backed execution boundaries + multi-agent execution discipline**

FS is moving from descriptive execution planning toward a verified execution loop. Linux namespace capability probes are explicit runtime evidence, boundary guarantees deterministically become required verification checks, and the transaction layer derives those checks instead of relying on callers to remember them.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | workspace backend | `src/fs_overlay/isolation.py`, `src/fs_overlay/linux_executor.py`, `tests/test_isolation.py`, `tests/test_linux_executor.py` | `ec209dc69c3a1851061438a3898cc0e4f96e0de4` | backend integrated, CI pending | Observe CI; then connect backend-specific execution evidence without using a generic temporary probe as proof of another execution |

## Recently completed

### Namespace identity verification

- `probe_namespace()` executes a disposable namespace child and observes `/proc/self/ns/<type>` inside it.
- A successful `unshare` exit is insufficient if the child reports the same namespace identity as the parent.
- PID probes use `--fork` so the observed child is actually inside the new PID namespace.

### Workspace boundary probe

- Added `src/fs_overlay/workspace_boundary.py` and tests.
- The disposable probe uses an explicitly installed bubblewrap backend when available.
- It creates a temporary workspace and verifies the workspace sentinel is visible while an unbound host-root path is absent.
- It is evidence for that disposable probe only, not for unrelated executions.

### Concrete workspace backend

- Added `BubblewrapWorkspaceBackend`.
- It requires Linux, an explicit workspace path, and bubblewrap >= 0.12.0.
- It constructs a new filesystem namespace with the workspace exposed at `/workspace` and a minimal read-only runtime allowlist.
- It rejects missing/relative/non-directory workspace paths.
- It never silently falls back to privileged setup or another isolation mechanism.
- `LinuxNamespaceExecutor` now accepts `workspace-only` with an explicit `workspace_path` through this backend; the existing host policy remains unchanged.

### Guarantee-to-check mapping

- `mount-namespace`, `pid-namespace`, and `network-namespace` map to explicit namespace verification checks.
- `workspace-binding-admitted` remains deliberately unmapped because the transaction evidence path does not yet attest that the exact execution used the concrete workspace backend.

## Validation state

- CI run `34437693909`: PASS, Python 3.11/3.12/3.13.
- CI run `34438066397` is in progress for the workspace executor commit chain.
- CI run `34438073158` is queued for the latest isolation test commit.
- No PASS is claimed for the new backend until those runs complete.

## Recommended next implementation step

1. Observe CI for the latest commits.
2. Extend execution evidence so a successful workspace execution carries backend identity and exact workspace-boundary observations.
3. Only then map `workspace-binding-admitted` to a required `workspace:boundary` check.
4. Keep the generic disposable workspace probe as capability/evidence validation, not as a substitute for post-execution evidence.
5. Run the complete matrix again after evidence integration.

## Known non-goals for this phase

- Do not implement privileged namespace creation.
- Do not assume `unshare` proves workspace isolation.
- Do not silently introduce user namespaces as a fallback.
- Do not mutate host-wide cgroups.
- Do not claim resource enforcement without an enforceable FS-owned/delegated resource lease.
- Do not turn FS-IR directly into host mutation without authority, admission, execution, observation, and verification gates.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
