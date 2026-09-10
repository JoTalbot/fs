# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `073299ec60eeb8d85ea0764e21dce4d088849707`
- Latest documentation commit: `97cc3ca11756316539861ce2f2abb727febc6cc5`
- Updated: 2026-09-10

## Current architectural phase

**Release hardening / cross-platform execution boundaries**

Linux has the evidence-backed reference runtime. Windows has a native Job Object resource backend with per-execution handles, native limits and read-back verification, plus a real Windows-only kernel round-trip test. macOS has a signed/entitled helper admission boundary and CI coverage. FreeBSD has a native Capsicum capability-mode adapter, kernel read-back, an isolated child-process test, and a native C helper that opens the target before `cap_enter()`, limits its executable descriptor, verifies capability mode, proves global filesystem lookup is blocked, then uses `fexecve()`.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | Release hardening | none | `97cc3ca11756316539861ce2f2abb727febc6cc5` | HANDED_OFF / blocked only on external native FreeBSD observation and release publication | Observe Cirrus FreeBSD 14.3 native task when externally available; then publish/tag the release through a GitHub release-capable control surface |

## Completed in this batch

- Added `MacOSSignedHelperBackend`, which validates a signed App Sandbox host/helper packaging boundary using `codesign` and never claims the current Python process is sandboxed.
- Required the macOS helper contract to expose App Sandbox + inheritance entitlements and hardened runtime evidence.
- Added `FreeBSDCapsicumBackend` using native `cap_enter()` followed by `cap_getmode()` read-back in the workload process.
- Added an isolated FreeBSD-native child-process round-trip test so `cap_enter()` cannot sandbox the pytest supervisor process itself.
- Added versioned macOS and FreeBSD backend contracts and explicit evidence markers.
- Added cross-platform tests for macOS and FreeBSD fail-closed behavior and macOS artifact admission.
- Expanded GitHub CI from Ubuntu/Windows to Ubuntu/Windows/macOS across Python 3.11/3.12/3.13.
- Added `.cirrus.yml` targeting a real FreeBSD 14.3 VM for native Capsicum testing.
- Added `native/freebsd/capsicum_exec.c`: a minimal native helper that resolves the target before entering capability mode, restricts its descriptor to `CAP_READ` + `CAP_FEXECVE`, verifies kernel capability mode, proves absolute global filesystem lookup is rejected, and replaces itself with the target via `fexecve()`.
- Extended `tests/test_freebsd_capsicum.py` to require the new `capsicum-global-namespace-blocked` evidence marker.
- Documented the helper execution boundary and the distinction between native FreeBSD validation and the still-unobserved external Cirrus result.

## Research / decision evidence

- FreeBSD `cap_enter(2)`: capability mode applies to the calling process and descendants; `cap_getmode()` provides kernel state read-back; effective sandboxes require deliberate capability-right preparation.
- FreeBSD `cap_rights_limit(2)`: capability rights can only be reduced, never expanded; the helper therefore pre-opens the target and limits its descriptor before entering capability mode.
- FreeBSD `open(2)`: an absolute global path opened after entering capability mode is rejected with `ECAPMODE`/`ENOTCAPABLE`, giving a direct negative kernel-enforcement assertion.
- Cirrus CI officially supports `freebsd_instance` with `freebsd-14-3`; the repository already has `.cirrus.yml`. Native execution depends on the externally connected Cirrus service.
- Agent Skills specification was checked; no external skill materially fits this kernel-boundary implementation, so `no suitable external skill found`. Local `fs-agent-core` remains authoritative.

## Validation

- Previously observed CI #120 `34451098521`: PASS on Ubuntu 3.11/3.12/3.13, Windows 3.11/3.12/3.13 and macOS 3.11/3.12/3.13.
- GitHub combined status for the new implementation/documentation heads is empty. No new GitHub CI result is claimed.
- Local execution was attempted but the environment cannot resolve `github.com`, so the repository could not be cloned for local pytest execution. No local test pass is claimed.
- Static repository inspection confirms `.github/workflows/ci.yml` covers Ubuntu/Windows/macOS with Python 3.11/3.12/3.13 and `.cirrus.yml` covers FreeBSD 14.3.
- No FreeBSD kernel execution result is claimed yet. The native task must be observed in Cirrus.
- GitHub currently reports zero published releases for `JoTalbot/fs`.

## Release posture

The repository is suitable for a **reference-architecture / preview release**, not an assertion of full production readiness. README and execution-runtime documentation intentionally state that the storage engine, full production lifecycle/recovery/federation scheduler, and native FreeBSD execution evidence remain outside the current validated production scope. This is a deliberate truthfulness boundary, not a hidden failure.

## Safety constraints

- Never claim a native backend from an API wrapper alone.
- Native resource limits require exact application/read-back evidence, matching the Linux cgroup contract.
- Unsupported platforms and limits fail closed.
- Job Object resource control must not be advertised as filesystem/network isolation.
- macOS must use a signed/entitled runtime boundary; do not substitute undocumented generic sandbox commands.
- macOS helper artifact validation is not execution evidence until a signed sandbox host launches the helper.
- Capsicum evidence must be produced by the workload process; never enter capability mode in the supervisor parent as a substitute.
- FreeBSD target resolution must occur before `cap_enter()`; use a pre-opened descriptor and `fexecve()` rather than resolving the target path after entering capability mode.
- Never introduce privilege escalation or user namespaces as a portability workaround.
- Do not emulate FreeBSD with a Linux/macOS platform override to manufacture native-kernel evidence.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
