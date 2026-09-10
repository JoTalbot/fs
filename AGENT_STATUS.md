# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `b186b3b6b48f79e7def64e7b0902f846b8b9641f`
- Updated: 2026-09-10

## Current architectural phase

**Cross-platform execution backend contracts / FreeBSD helper boundary**

Linux has the evidence-backed reference runtime. Windows has a native Job Object resource backend with per-execution handles, native limits and read-back verification, plus a real Windows-only kernel round-trip test. macOS has a signed/entitled helper admission boundary and CI coverage. FreeBSD now has a native Capsicum capability-mode adapter, kernel read-back, an isolated child-process test, and a native C helper design that opens the target before `cap_enter()`, limits its executable descriptor, verifies capability mode, then uses `fexecve()`.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | FreeBSD execution boundary | `native/freebsd/capsicum_exec.c`, `tests/test_freebsd_capsicum.py`, `.cirrus.yml` | `e52232a9aaf340475f13295cdb29f19f2404e970` | helper implemented; native execution still unobserved | Run/observe the real FreeBSD task, then integrate the helper into a platform-specific supervisor adapter only after native evidence is green |

## Completed in this batch

- Added `MacOSSignedHelperBackend`, which validates a signed App Sandbox host/helper packaging boundary using `codesign` and never claims the current Python process is sandboxed.
- Required the macOS helper contract to expose App Sandbox + inheritance entitlements and hardened runtime evidence.
- Added `FreeBSDCapsicumBackend` using native `cap_enter()` followed by `cap_getmode()` read-back in the workload process.
- Added an isolated FreeBSD-native child-process round-trip test so `cap_enter()` cannot sandbox the pytest supervisor process itself.
- Added versioned macOS and FreeBSD backend contracts and explicit evidence markers.
- Added cross-platform tests for macOS and FreeBSD fail-closed behavior and macOS artifact admission.
- Expanded CI from Ubuntu/Windows to Ubuntu/Windows/macOS across Python 3.11/3.12/3.13.
- Added `.cirrus.yml` targeting a real FreeBSD 14.3 VM for native Capsicum testing.
- Added `native/freebsd/capsicum_exec.c`: a minimal native helper that resolves the target before entering capability mode, restricts the target descriptor to `CAP_READ` + `CAP_FEXECVE`, verifies kernel capability mode, and replaces itself with the target via `fexecve()`.
- Extended the FreeBSD native test to compile the helper with `-Wall -Wextra -Werror` and execute `/bin/echo` through the helper, checking both workload output and helper evidence markers.

## Research / decision evidence

- FreeBSD `cap_enter(2)`: capability mode applies to the calling process and descendants; `cap_getmode()` provides kernel state read-back; effective sandboxes require deliberate capability-right preparation. citeturn0search1
- FreeBSD `cap_rights_limit(2)` and rights documentation: capability rights can only be reduced; `CAP_FEXECVE` permits `fexecve()` and requires `CAP_READ`. citeturn0search3turn2search1
- FreeBSD `fexecve(2)`: execution can be driven from an already-open executable descriptor rather than resolving a path after entering the sandbox. citeturn1search10
- FreeBSD documentation explicitly recommends `fexecve()` when constructing a carefully controlled runtime environment because inherited rights must be considered. citeturn0search1
- Skill discovery found no external skill materially applicable to this FreeBSD kernel-boundary implementation; local `fs-agent-core` remains authoritative.

## Validation

- CI #120 `34451098521`: PASS on Ubuntu 3.11/3.12/3.13, Windows 3.11/3.12/3.13 and macOS 3.11/3.12/3.13.
- `.cirrus.yml` was committed successfully as `e52232a9aaf340475f13295cdb29f19f2404e970`.
- Native helper source and test commits succeeded: `ed7f92392df17d6162747e58e48b77e375b9fbf2` and `b186b3b6b48f79e7def64e7b0902f846b8b9641f`.
- No FreeBSD kernel execution result is claimed yet. GitHub workflow lookup for `b186b3b6b48f79e7def64e7b0902f846b8b9641f` returned no GitHub Actions workflow runs; the native task is hosted by Cirrus and must be observed there.

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
