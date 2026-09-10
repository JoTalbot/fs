# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `03525189eeb617f28c85b6c2dcaddfe28ffe3f1e`
- Updated: 2026-09-10

## Current architectural phase

**Cross-platform execution backend contracts**

Linux has the evidence-backed reference runtime. Windows has a native Job Object resource backend with per-execution handles, native limits and read-back verification, plus a real Windows-only kernel round-trip test. CI now exercises both Ubuntu and Windows across Python 3.11/3.12/3.13. Capability negotiation and versioned backend contracts are present. macOS and BSD remain explicitly fail-closed until their native runtime mechanisms can provide equivalent execution evidence.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | cross-platform execution | isolation/cgroup/runtime test portability and Windows resource/isolation boundary | `79851885b86e6929530e4ae74d9b42455054af5d` | fixed cross-platform test assumptions; latest CI pending | Validate latest six-platform jobs, then proceed to signed macOS helper/runtime and BSD/Capsicum adapter design without false generic fallbacks |

## Completed in this batch

- Added Windows CI coverage and native Job Object round-trip testing.
- Diagnosed the first Windows CI run: six failures were cross-platform test assumptions, not native Job Object API failures.
- Made the cgroup lease-admission test explicitly model Linux before asserting Linux behavior.
- Scoped bubblewrap and Linux namespace tests to Linux; Windows runners no longer attempt `/proc` namespace operations.
- Scoped the end-to-end `ExecutionRuntime` commit test to Linux because the current runtime is explicitly a Linux runtime.
- Corrected the legacy Windows isolation facade: Job Objects are resource/process control, not filesystem/network isolation. The isolation facade now fails closed until a genuine Windows filesystem/network boundary exists, while the native resource backend remains available separately.
- Corrected the Windows fail-closed resource test so it tests the non-Windows contract without depending on the host OS.

## Research / decision evidence

- Microsoft Job Object documentation confirms native `SetInformationJobObject`, `QueryInformationJobObject`, and `AssignProcessToJobObject` are the relevant resource/process-control primitives. citeturn0search4turn0search10turn0search13
- Apple App Sandbox documentation confirms sandbox boundaries are entitlement/signing based and supports embedded sandboxed helper tools; generic POSIX commands are not an equivalent macOS sandbox boundary. citeturn0search0turn0search1turn0search2
- Agent Skills specification and testing guidance confirm skills are reusable `SKILL.md` workflows and that platform-specific tests should be explicit rather than relying on incidental host behavior. citeturn1search0turn1search2turn1search7

## Validation

- CI #102 `34448825327`: Ubuntu 3.13 failed on stale `os.name` monkeypatch tests; Windows jobs were executing.
- CI #103 `34448840104`: Ubuntu 3.11/3.12/3.13 passed; Windows 3.11/3.12/3.13 exposed six cross-platform test assumptions. Native Windows runner was confirmed as Windows Server 2025 and reached the full pytest suite.
- Latest fixes are on `03525189eeb617f28c85b6c2dcaddfe28ffe3f1e`; CI validation is pending and no green result is claimed yet.

## Safety constraints

- Never claim a native backend from an API wrapper alone.
- Native resource limits require exact application/read-back evidence, matching the Linux cgroup contract.
- Unsupported platforms and limits fail closed.
- Job Object resource control must not be advertised as filesystem/network isolation.
- macOS must use a signed/entitled runtime boundary; do not substitute undocumented generic sandbox commands.
- Never introduce privilege escalation or user namespaces as a portability workaround.
- Windows native kernel validation must come from a real Windows runner/host, not Linux platform monkeypatching.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
