# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Last known head: `996b92647aa3c48845140428b0bd136adb7ad64c`
- Updated: 2026-09-10

## Current architectural phase

**Evidence-backed execution boundaries + multi-agent execution discipline**

FS is moving from descriptive execution planning toward a verified execution loop. Linux namespace capability probes are explicit runtime evidence, boundary guarantees deterministically become required verification checks, and the transaction layer derives those checks instead of relying on callers to remember them.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | Linux isolation evidence | `src/fs_overlay/linux_probe.py`, `tests/test_linux_probe.py`, `docs/LINUX_CAPABILITY_PROBES.md` | `ada1cf9d453179fd705fc13464882e40fcfaeba6` | completed implementation, CI pending | Run full CI matrix, then build concrete workspace-boundary probe |

## Recently completed

### Namespace identity verification

- `probe_namespace()` now executes a disposable namespace child and observes `/proc/self/ns/<type>` inside it.
- A successful `unshare` exit is insufficient if the child reports the same namespace identity as the parent.
- PID probes use `--fork` so the observed child is actually inside the new PID namespace.
- Tests cover both fail-closed unchanged identity and successful changed identity.
- Documentation now states the exact evidence scope and the remaining workspace-isolation gap.

### Probe-to-verification bridge

- Added `src/fs_overlay/probe_verification.py`.
- Added `tests/test_probe_verification.py`.
- Updated `docs/TRANSACTION_EXECUTOR.md`.
- Linux checks use explicit `namespace:<mount|pid|net>` identifiers.

### Guarantee-to-check mapping

- Added `src/fs_overlay/verification_requirements.py`.
- Added `tests/test_verification_requirements.py`.
- `mount-namespace`, `pid-namespace`, and `network-namespace` guarantees map deterministically to required namespace verification checks.
- Unmapped guarantees do not silently create fake evidence requirements.

### Transaction integration

- Added `src/fs_overlay/evidence_provider.py`.
- `TransactionExecutor` derives required checks from the admitted plan before commit.
- Caller-supplied checks may add requirements but cannot omit plan-derived requirements.
- Missing or failed required evidence prevents commit.
- The reference evidence provider dispatches exact Linux namespace checks to the disposable namespace probe.

### CI baseline

- Added `.github/workflows/ci.yml`.
- CI runs the complete pytest suite on every push to `main` and every pull request.
- CI covers Python 3.11, 3.12, and 3.13 on `ubuntu-latest`.
- Previous CI run `34437539759` passed all three Python jobs after the network-warning assertion fix.
- A new CI run is expected from the namespace identity probe changes; its result is not claimed until checked.

## Research record for current phase

- `unshare(1)` and `unshare(2)` document that namespace creation can be privilege-gated and that PID namespace observation requires a child process. citeturn0search0turn0search2
- `mount_namespaces(7)` documents mount namespace separation and propagation semantics. citeturn0search1
- Maintained container tooling observes/manages namespace handles directly rather than treating `unshare` availability as proof. citeturn1search0
- Local `linux-isolation-verification` skill requires exact evidence scope and fail-closed behavior. fileciteturn40file0

## Validation state

- CI run `34437539759`: PASS, Python 3.11/3.12/3.13.
- Namespace identity implementation: committed; new CI result pending.
- No claim is made yet about concrete workspace bind-mount/root filesystem isolation.

## Recommended next implementation step

1. Check the new CI run for the current `main` head.
2. If green, design a disposable workspace-boundary probe that tests the exact property FS claims, not merely mount namespace creation.
3. Keep user namespace support explicit and fail-closed; never add privilege escalation as a fallback.
4. Integrate workspace evidence only with an explicit guarantee/check mapping.
5. Run the full suite and record actual results.

## Known non-goals for this phase

- Do not implement privileged namespace creation.
- Do not assume `unshare` proves workspace isolation.
- Do not mutate host-wide cgroups.
- Do not claim resource enforcement without an enforceable FS-owned/delegated resource lease.
- Do not turn FS-IR directly into host mutation without authority, admission, execution, observation, and verification gates.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
