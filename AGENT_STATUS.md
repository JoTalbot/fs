# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation commit: `1d2065f1a9ffa0905c184fed2162c282bb51a8cc`
- Updated: 2026-09-10

## Current architectural phase

**Cross-platform execution backend contracts**

Linux has the evidence-backed reference runtime. Windows now has a native Job Object resource backend with per-execution handles, native limits and read-back verification. Capability negotiation and versioned backend contracts are present. macOS and BSD remain explicitly fail-closed until their native runtime mechanisms can provide equivalent execution evidence.

## Active work registry

| Agent | Machine | Area | Claimed files | Base commit | Status | Next step |
|---|---|---|---|---|---|---|
| current-agent | ChatGPT | cross-platform execution | Windows Job Object, capability negotiation, backend contract, runtime docs/status/log | `620078fd9e740832df773221270947a4bb39fe36` | implementation complete; CI #99 running | Validate final head, then proceed to signed macOS helper/runtime and BSD/Capsicum adapter design without false generic fallbacks |

## Completed in this batch

- Implemented native Windows Job Object enforcement for CPU hard-cap, job memory and active-process limits.
- Windows backend creates a per-execution Job Object, assigns the child process, queries limits back, retains the Job handle through execution, and releases it after completion.
- Corrected Windows process handle rights to the rights required for Job Object assignment.
- Unsupported disk limits and invalid budgets fail closed.
- ProcessSupervisor now selects the native resource backend by platform and releases backend-owned resources after execution.
- Added conservative platform capability negotiation.
- Added versioned backend contracts for Bubblewrap, Linux cgroup v2 and Windows Job Objects.
- Documented the macOS signed-runtime boundary and BSD native-adapter boundary without claiming generic POSIX isolation.

## Validation

- CI #92 `34446735409`: PASS, Python 3.11/3.12/3.13, Windows backend and supervisor changes.
- CI #94 `34446749651`: FAILED because capability tests temporarily coupled Windows detection to a monkeypatched `os.name` on Linux; this was diagnosed and corrected in `e0bde8db01e4faeffa603a5bd46bbf837837617a`.
- CI #97 `34446816202`: queued for versioned backend contract tests.
- CI #98 `34446828655`: queued for cross-platform documentation/capability head.
- CI #99 `34446853590`: in progress for final Windows handle-rights correction and current implementation head.

## Safety constraints

- Never claim a native backend from an API wrapper alone.
- Native resource limits require exact application/read-back evidence, matching the Linux cgroup contract.
- Unsupported platforms and limits fail closed.
- macOS must use a signed/entitled runtime boundary; do not substitute undocumented generic sandbox commands.
- Never introduce privilege escalation or user namespaces as a portability workaround.

## Handoff rule

Any agent taking work from this file must first update the active work registry with its own identity, claimed files, base commit, and intended step. On completion, replace the entry with the result, validation evidence, commit SHA, and next action.
