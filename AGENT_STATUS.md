# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `513f03776b86f0710e6892ad52734c9411b714b0`
- Updated: 2026-09-10

## Current architectural phase

**Release hardening / FreeBSD helper boundary**

Linux has the evidence-backed reference runtime. Windows has a native Job Object resource backend with per-execution handles, native limits and read-back verification, plus a real Windows-only kernel round-trip test. macOS has a signed/entitled helper admission boundary and CI coverage. FreeBSD has a native Capsicum capability-mode adapter, kernel read-back, an isolated child-process test, and a native C helper that opens the target before `cap_enter()`, limits its executable descriptor, verifies capability mode, then uses `fexecve()`.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | FreeBSD release hardening | `native/freebsd/capsicum_exec.c`, `tests/test_freebsd_capsicum.py`, `docs/EXECUTION_RUNTIME.md` | `513f03776b86f0710e6892ad52734c9411b714b0` | CLAIMED / RESEARCHED | Add an explicit negative global-namespace enforcement assertion to the native helper path, validate the complete release test matrix where executable, then record the remaining external FreeBSD/Cirrus gate without manufacturing evidence |

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

- FreeBSD `cap_enter(2)`: capability mode applies to the calling process and descendants; `cap_getmode()` provides kernel state read-back; effective sandboxes require deliberate capability-right preparation. Official FreeBSD 14.3 manual.
- FreeBSD `cap_rights_limit(2)`: capability rights can only be reduced, never expanded; the helper therefore pre-opens the target and limits its descriptor before entering capability mode.
- FreeBSD `open(2)`: in capability mode, global-path `open()` is rejected with capability errors, providing a direct negative enforcement assertion for the helper.
- Cirrus CI officially supports `freebsd_instance` with `freebsd-14-3`; the repository already has `.cirrus.yml`. Native execution still depends on an externally connected Cirrus service, which is not exposed through the current GitHub connector.
- Agent Skills specification confirms reusable skills are centered on `SKILL.md`; repository-local `fs-agent-core` remains authoritative. No external skill materially fits this kernel-boundary implementation, so `no suitable external skill found`.

## Validation

- CI #120 `34451098521`: PASS on Ubuntu 3.11/3.12/3.13, Windows 3.11/3.12/3.13 and macOS 3.11/3.12/3.13.
- `.cirrus.yml` was committed successfully.
- Native helper source and test commits succeeded: `ed7f92392df17d6162747e58e48b77e375b9fbf2` and `b186b3b6b48f79e7def64e7b0902f846b8b9641f`.
- Current `main` head is `513f03776b86f0710e6892ad52734c9411b714b0`.
- GitHub combined status for the current head is empty, so no new GitHub CI result is claimed here.
- No FreeBSD kernel execution result is claimed yet. The native task is hosted by Cirrus and must be observed there.

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
