# FS Agent Log

Append concise, durable work records here. This is not a raw chat transcript. Each entry should let another agent understand what happened, why, what evidence exists, and what knowledge should be reused.

## Entry format

```text
## YYYY-MM-DD HH:MM UTC | agent_id | step-id
Base: <commit>
Area: <area>
Goal: <goal>
Research:
- <source> -> <finding>
Skill discovery:
- <skill/source> -> <adopted/rejected and why>
Changes:
- <change>
Validation:
- <actual validation>
Result: <commit or no-commit reason>
Learning:
- [RULE|PATTERN|FAILURE|RESEARCH|TOOLING|SECURITY|ARCHITECTURE] <durable lesson>
Next: <exact next safe step>
```

## 2026-09-10 | bootstrap | multi-agent-contract
Base: 7c6ff25ed34c92213c249a2944667ee85f19fe66
Area: agent coordination
Goal: Establish a repository-level operating contract for concurrent AI agents on different machines.
Research:
- Agent Skills specification -> skills are filesystem-based reusable workflows with `SKILL.md` as the core contract.
- Microsoft VS Code agent customization -> root `AGENTS.md` is intended as shared guidance for multiple AI coding agents.
- Public AGENTS.md examples -> canonical repository guidance plus explicit reconnaissance/validation and skill organization are established patterns.
Skill discovery:
- Agent Skills repositories searched; project now requires discovery before every substantive step.
Changes:
- Added `AGENTS.md`.
- Added `AGENT_STATUS.md`.
- Added this append-only learning log.
Validation:
- Repository state checked through GitHub after previous transaction-verification work.
Result: see subsequent commits in `main`.
Learning:
- [RULE] Repository state, not private agent conversation, is the shared source of truth.
- [RULE] Parallel agents must declare file/area ownership and hand off through persistent status.
- [RULE] Research and skill discovery are mandatory gates before substantive work.
Next: Create and maintain the canonical `fs-agent-core` skill, then continue evidence-backed execution work.

## 2026-09-14 | current-agent | replay-concurrency-hardening
Base: ac3f9bfe29895e2d2fd3547206e083cee8798018
Area: federation replay admission
Goal: Ensure one in-process receiver cannot concurrently admit the same federation envelope more than once.
Research:
- Current `federation_protocol.py` and `test_federation_protocol.py` were re-read from `main` before implementation.
- Existing `DurableFederationState` already serializes its own durable admission critical section; `ReplayGuard` did not serialize its check-and-record operation.
Skill discovery:
- No external skill materially fit this protocol-concurrency step; repository `fs-agent-core` and existing federation invariants remained authoritative.
Changes:
- Added a process-local lock to `ReplayGuard` and held it across duplicate-ID and sender-sequence checks plus state mutation.
- Added a deterministic 16-thread receiver regression test requiring exactly one successful admission for the same signed envelope.
- Updated shared status to record the new invariant and validation target.
Validation:
- GitHub writes succeeded.
- Full CI for the new head is pending; no test pass is claimed yet.
Result: implementation `05747ab970b292f42e25ebd46531e1c79e360398`; test `b2d7ebc3838807727144ba12febaabb86a734dd2`; status `0db9a5b496730bc43ba61b7ca7d98d2ef1cb6c57`.
Learning:
- [SECURITY] Replay prevention is a check-and-record invariant; locking only one side is insufficient because concurrent receivers can otherwise observe the same unused state.
- [RULE] Process-local replay protection is not a substitute for the existing durable/cross-process coordination boundary.
Next: Validate the full CI matrix for this hardening, then continue Phase 2 with the next explicit recovery invariant.

## 2026-09-14 | current-agent | windows-coordination-fix
Base: 339f867dac46126dfcd5e1333d8ab1ed37f9ccf1
Area: cross-process durable admission coordination
Goal: Fix the Windows-only race exposed by the transaction crash qualification CI run.
Research:
- CI #371 (`34853694239`) on Windows Python 3.13 failed in `test_coordinated_processes_refresh_stale_admission_state` with `PermissionError: [Errno 13] Permission denied` during the buffered `handle.flush()` used to prepare the lock file.
- Python `msvcrt.locking` documentation -> the lock region may extend beyond EOF, so a pre-existing zero-length lock file does not require a buffered sentinel write before byte-range locking.
Changes:
- Replaced the Windows buffered sentinel-write path with `Path.touch(exist_ok=True)` followed by `r+b` open and direct byte-zero `msvcrt.locking`.
- Preserved retained lock paths, automatic OS lock release after process crash, bounded timeout, and no stale-lock stealing.
Validation:
- CI #372 (`34853735052`): **18/18 jobs passed** across Ubuntu/Windows/macOS and Python 3.11/3.12/3.13, including candidate crypto-provider jobs.
Result: implementation `010685c84c3f9eebc1f5a0cf8643919df454d970`; status `fc76867b6602f78fca476a311e937ce05a89d1cf`.
Learning:
- [FAILURE] Windows file coordination must not depend on a concurrent buffered mutation of the shared lock path.
- [RULE] Keep the lock file as durable coordination metadata, but make acquisition itself an OS-level byte-range operation with no pre-lock buffered write.
Next: Continue Phase 2 with remaining explicit journal/crash boundaries and deterministic multi-node fixtures.

## 2026-09-14 | current-agent | replica-recovery-hardening
Base: 010685c84c3f9eebc1f5a0cf8643919df454d970
Area: failure-domain-aware replica placement and recovery
Goal: Ensure failed replicas do not falsely satisfy the desired durable copy count during recovery.
Research:
- Current `replication_policy.py` and `test_replication_policy.py` were re-read from `main` before implementation.
- Existing policy already prioritizes new failure domains, but its copy-count calculation used all `present_on` nodes, including unhealthy or unknown nodes.
Skill discovery:
- Repository `fs-agent-core` and existing replication invariants remained authoritative; no external skill was needed for this deterministic policy correction.
Changes:
- Materialized candidates once so present-node health can be evaluated consistently.
- Count only healthy present candidates toward `desired_copies`.
- Use only healthy present candidates when reserving existing failure domains, allowing recovery into a different domain after failure.
- Added regressions for an unhealthy present replica and an unknown present node.
Validation:
- GitHub Actions CI #376 (`34855160140`) was started for implementation `e2c1f600aee58fd9b90a546a7164499eac0091d1`; it was still **in progress** when this record was written.
Result: implementation `e2c1f600aee58fd9b90a546a7164499eac0091d1`; tests `1547bd838c16861e98335f5b539e831d3b947b2a`; status `a1b67609506bf44a5a8dd863d04b55da0c57ff3f`.
Learning:
- [FAILURE] Replica recovery must distinguish healthy durable copies from nodes merely listed as present.
- [RULE] Failed or unknown placement state must never reduce the number of required healthy replicas or block failure-domain diversity.
Next: Validate CI #376, then build deterministic two-node and three-node federation fixtures and continue explicit journal/crash qualification.
