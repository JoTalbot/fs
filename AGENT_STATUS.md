# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `79851885b86e6929530e4ae74d9b42455054af5d`
- Updated: 2026-09-10

## Current architectural phase

**Cross-platform execution backend contracts**

Linux has the evidence-backed reference runtime. Windows now has a native Job Object resource backend with per-execution handles, native limits and read-back verification, plus a real Windows-only kernel round-trip test. CI now exercises both Ubuntu and Windows across Python 3.11/3.12/3.13. Capability negotiation and versioned backend contracts are present. macOS and BSD remain explicitly fail-closed until their native runtime mechanisms can provide equivalent execution evidence.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | cross-platform execution | Windows Job Object, CI, native Windows test, capability negotiation, backend contract, runtime docs/status | `21ec652c92205a36762aef8d049039e56f2f6f23` | Windows validation batch submitted; CI pending | Validate new cross-platform CI, then proceed to signed macOS helper/runtime and BSD/Capsicum adapter design without false generic fallbacks |

## Completed in this batch

- Added `windows-latest` to the CI matrix alongside Ubuntu for Python 3.11/3.12/3.13.
- Added a Windows-only native kernel round-trip test that spawns a real child process, applies an active-process Job Object limit, verifies the configured limit through the native query path, and releases the per-execution handle.
- Preserved fail-closed contract tests for non-Windows hosts and mocked platform planning.
- Kept Windows disk enforcement explicitly unsupported rather than inventing an unverified mapping.

## Validation

- Prior CI #92 `34446735409`: PASS, Python 3.11/3.12/3.13, Windows backend and supervisor changes.
- Prior CI #94 `34446749651`: FAILED because capability tests temporarily coupled Windows detection to a monkeypatched `os.name` on Linux; corrected in `e0bde8db01e4faeffa603a5bd46bbf837837617a`.
- Prior CI #97 `34446816202`: queued for versioned backend contract tests.
- Prior CI #98 `34446828655`: queued for cross-platform documentation/capability head.
- Prior CI #99 `34446853590`: was running for the previous Windows handle-rights head.
- Current CI for commit `79851885b86e6929530e4ae74d9b42455054af5d`: pending after adding native Windows runner coverage.

## Safety constraints

- Never claim a native backend from an API wrapper alone.
- Native resource limits require exact application/read-back evidence, matching the Linux cgroup contract.
- Unsupported platforms and limits fail closed.
- macOS must use a signed/entitled runtime boundary; do not substitute undocumented generic sandbox commands.
- Never introduce privilege escalation or user namespaces as a portability workaround.
- Windows native kernel validation must come from a real Windows runner/host, not Linux platform monkeypatching.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
