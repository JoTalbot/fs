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
