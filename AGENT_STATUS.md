# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest work chain: `96e82ad989543cf7bd5e486ada08b9b7b8b38409` → `7cba73e398ad8a224fdc8bc026c64582f5361b9c` → `5c99eaa317c3322a285eca00b002db4c45fb487a`
- Updated: 2026-09-10

## Current architectural phase

**Evidence-backed execution boundaries + multi-agent execution discipline**

FS is moving from descriptive execution planning toward a verified execution loop. Linux namespace capability probes are explicit runtime evidence, boundary guarantees deterministically become required verification checks, and the transaction layer derives those checks instead of relying on callers to remember them.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | workspace boundary evidence | `src/fs_overlay/workspace_boundary.py`, `tests/test_workspace_boundary.py`, `docs/LINUX_CAPABILITY_PROBES.md` | `612211a9d66fa70f86cfbf05801a2607a3a1b8c4` | probe implemented, CI pending | Integrate the same concrete backend into execution before mapping `workspace-binding-admitted` to evidence |

## Recently completed

### Namespace identity verification

- `probe_namespace()` executes a disposable namespace child and observes `/proc/self/ns/<type>` inside it.
- A successful `unshare` exit is insufficient if the child reports the same namespace identity as the parent.
- PID probes use `--fork` so the observed child is actually inside the new PID namespace.

### Workspace boundary evidence probe

- Added `src/fs_overlay/workspace_boundary.py`.
- Added `tests/test_workspace_boundary.py`.
- The probe uses an explicitly installed `bubblewrap` backend when available.
- It creates a temporary workspace and verifies from inside the sandbox that the workspace sentinel is visible while an unbound host-root path is absent.
- Backend absence or kernel rejection fails closed.
- The probe does not yet imply that the FS execution backend uses the same boundary.

### Guarantee-to-check mapping

- `mount-namespace`, `pid-namespace`, and `network-namespace` map to explicit namespace verification checks.
- `workspace-binding-admitted` remains deliberately unmapped because the execution path does not yet consume the concrete workspace boundary backend.

## Research record for current phase

- Bubblewrap documentation describes an unprivileged sandbox with a new filesystem namespace and explicit bind mounts; user namespace creation is required when bwrap is not installed setuid root.
- FS therefore treats bubblewrap as an explicit backend capability, never as an invisible privilege workaround.
- The local Linux isolation skill requires exact evidence scope and fail-closed behavior.

## Validation state

- CI run `34437693909`: PASS, Python 3.11/3.12/3.13.
- Workspace boundary probe commits are newer than that run; their CI result is not claimed until observed.
- No claim is made yet that `workspace-only` execution is safely enforced by the concrete executor.

## Recommended next implementation step

1. Integrate the workspace backend into the concrete Linux executor with an explicit workspace path.
2. Make execution admission depend on the backend's actual availability, not merely `unshare` presence.
3. Route the exact workspace probe through the evidence provider only for executions that used that backend.
4. Only then map `workspace-binding-admitted` to `workspace:boundary` verification.
5. Run the full CI matrix and record actual results.

## Known non-goals for this phase

- Do not implement privileged namespace creation.
- Do not assume `unshare` proves workspace isolation.
- Do not silently introduce user namespaces as a fallback.
- Do not mutate host-wide cgroups.
- Do not claim resource enforcement without an enforceable FS-owned/delegated resource lease.
- Do not turn FS-IR directly into host mutation without authority, admission, execution, observation, and verification gates.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
