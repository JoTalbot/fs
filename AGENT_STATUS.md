# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `e52232a9aaf340475f13295cdb29f19f2404e970`
- Updated: 2026-09-10

## Current architectural phase

**Cross-platform execution backend contracts**

Linux has the evidence-backed reference runtime. Windows has a native Job Object resource backend with per-execution handles, native limits and read-back verification, plus a real Windows-only kernel round-trip test. macOS now has a signed/entitled helper admission boundary and CI coverage. FreeBSD now has a native Capsicum capability-mode adapter with kernel read-back and an isolated native child-process test path, while generic supervisor integration remains deliberately deferred until a dedicated helper boundary exists.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | FreeBSD native validation | `.cirrus.yml`, FreeBSD Capsicum test path | `03cbccd0ac93c56ee9c9fddc49b3d0d802e89385` | native CI configuration added; execution not yet observed | Enable/observe the Cirrus CI FreeBSD task on a real FreeBSD VM; do not claim native validation until the task is green |

## Completed in this batch

- Added `MacOSSignedHelperBackend`, which validates a signed App Sandbox host/helper packaging boundary using `codesign` and never claims the current Python process is sandboxed.
- Required the macOS helper contract to expose App Sandbox + inheritance entitlements and hardened runtime evidence.
- Added `FreeBSDCapsicumBackend` using native `cap_enter()` followed by `cap_getmode()` read-back in the workload process.
- Added an isolated FreeBSD-native child-process round-trip test so `cap_enter()` cannot sandbox the pytest supervisor process itself.
- Added versioned macOS and FreeBSD backend contracts and explicit evidence markers.
- Added cross-platform tests for macOS and FreeBSD fail-closed behavior and macOS artifact admission.
- Expanded CI from Ubuntu/Windows to Ubuntu/Windows/macOS across Python 3.11/3.12/3.13.
- Added `.cirrus.yml` targeting a real FreeBSD 14.3 VM for the native Capsicum child-process test.
- Updated execution runtime documentation to distinguish macOS artifact admission from actual sandboxed execution and to keep Capsicum separate from Linux network namespaces.

## Research / decision evidence

- FreeBSD documents `cap_enter()` as entering capability mode in the calling process, `cap_getmode()` as kernel state read-back, and inheritance of capability mode by descendants. Effective sandboxes also require deliberate rights preparation. citeturn0search1turn0search2
- Cirrus CI documents managed FreeBSD VMs through `freebsd_instance`, including FreeBSD 14.3 images, and explicitly supports FreeBSD virtual machines for open-source projects. citeturn2search0turn2search1
- FreeBSD documents package installation through `pkg`, and the current Python 3.11 package is available as `lang/python311`; the task uses the corresponding `python311` package and an isolated virtual environment. citeturn3search0turn3search9
- Agent Skills research found only generic Agent Skills authoring/testing skills; none materially fit FreeBSD kernel execution, so local `fs-agent-core` remains authoritative. citeturn0search3turn0search7

## Validation

- CI #120 `34451098521`: PASS on Ubuntu 3.11/3.12/3.13, Windows 3.11/3.12/3.13 and macOS 3.11/3.12/3.13.
- `.cirrus.yml` was committed successfully as `e52232a9aaf340475f13295cdb29f19f2404e970`.
- The Cirrus FreeBSD task has **not** been observed running yet, so no FreeBSD native kernel result is claimed.

## Safety constraints

- Never claim a native backend from an API wrapper alone.
- Native resource limits require exact application/read-back evidence, matching the Linux cgroup contract.
- Unsupported platforms and limits fail closed.
- Job Object resource control must not be advertised as filesystem/network isolation.
- macOS must use a signed/entitled runtime boundary; do not substitute undocumented generic sandbox commands.
- macOS helper artifact validation is not execution evidence until a signed sandbox host launches the helper.
- Capsicum evidence must be produced by the workload process; never enter capability mode in the supervisor parent as a substitute.
- Never introduce privilege escalation or user namespaces as a portability workaround.
- Do not emulate FreeBSD with a Linux/macOS platform override to manufacture native-kernel evidence.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
