# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `03cbccd0ac93c56ee9c9fddc49b3d0d802e89385`
- Updated: 2026-09-10

## Current architectural phase

**Cross-platform execution backend contracts**

Linux has the evidence-backed reference runtime. Windows has a native Job Object resource backend with per-execution handles, native limits and read-back verification, plus a real Windows-only kernel round-trip test. macOS now has a signed/entitled helper admission boundary and CI coverage. FreeBSD now has a native Capsicum capability-mode adapter with kernel read-back and an isolated native child-process test path, while generic supervisor integration remains deliberately deferred until a dedicated helper boundary exists.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | cross-platform execution | FreeBSD Capsicum native validation path, platform CI | `03cbccd0ac93c56ee9c9fddc49b3d0d802e89385` | validation batch complete; 9-way CI green | Validate the native FreeBSD child-process test on a real FreeBSD host; do not claim that result until observed |

## Completed in this batch

- Added `MacOSSignedHelperBackend`, which validates a signed App Sandbox host/helper packaging boundary using `codesign` and never claims the current Python process is sandboxed.
- Required the macOS helper contract to expose App Sandbox + inheritance entitlements and hardened runtime evidence.
- Added `FreeBSDCapsicumBackend` using native `cap_enter()` followed by `cap_getmode()` read-back in the workload process.
- Added an isolated FreeBSD-native child-process round-trip test so `cap_enter()` cannot sandbox the pytest supervisor process itself.
- Added versioned macOS and FreeBSD backend contracts and explicit evidence markers.
- Added cross-platform tests for macOS and FreeBSD fail-closed behavior and macOS artifact admission.
- Expanded CI from Ubuntu/Windows to Ubuntu/Windows/macOS across Python 3.11/3.12/3.13.
- Updated execution runtime documentation to distinguish macOS artifact admission from actual sandboxed execution and to keep Capsicum separate from Linux network namespaces.

## Research / decision evidence

- Apple documents App Sandbox as entitlement/signing based and documents embedding a sandboxed command-line helper with `com.apple.security.app-sandbox` and `com.apple.security.inherit`; hardened runtime is the supported runtime integrity boundary.
- Apple documents `codesign`/Code Signing Services as the supported way to validate signed code and requirements rather than encoding undocumented signature internals.
- FreeBSD documents `cap_enter()` as entering capability mode and `cap_getmode()` as the kernel read-back of that state; effective sandboxes also require deliberate capability/right preparation.
- GitHub currently provides macOS-hosted runners including `macos-latest`, so the macOS contract tests are exercised natively in CI.

## Validation

- CI #119 `34450652381`: PASS, Ubuntu 3.11/3.12/3.13, Windows 3.11/3.12/3.13, and macOS 3.11/3.12/3.13.
- macOS validation is now green on all three supported Python versions.
- No FreeBSD native kernel result is claimed yet; GitHub-hosted runner coverage does not include a standard FreeBSD label, so the native test is gated to a real FreeBSD host.

## Safety constraints

- Never claim a native backend from an API wrapper alone.
- Native resource limits require exact application/read-back evidence, matching the Linux cgroup contract.
- Unsupported platforms and limits fail closed.
- Job Object resource control must not be advertised as filesystem/network isolation.
- macOS must use a signed/entitled runtime boundary; do not substitute undocumented generic sandbox commands.
- macOS helper artifact validation is not execution evidence until a signed sandbox host launches the helper.
- Capsicum evidence must be produced by the workload process; never enter capability mode in the supervisor parent as a substitute.
- Never introduce privilege escalation or user namespaces as a portability workaround.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
