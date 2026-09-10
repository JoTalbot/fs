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
Goal: Establish a repository-level operating contract for concurrent agents on different machines.
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

## 2026-09-10 | current-agent | guarantee-verification-mapping
Base: ed05162607d042784ee18ad61073d938ea256d1b
Area: execution verification
Goal: Derive required verification checks from execution-boundary guarantees without inventing evidence.
Research:
- Current `execution_coordinator.py`, `network_namespace.py`, and `transaction_executor.py` were re-read from `main` before the change.
- Public Agent Skills repositories were searched before implementation; the project-level skill contract was created and adopted as the local baseline.
Changes:
- Added `src/fs_overlay/verification_requirements.py`.
- Added `tests/test_verification_requirements.py`.
- Mapped `mount-namespace`, `pid-namespace`, and `network-namespace` guarantees to explicit namespace verification checks.
- Deliberately left unmapped guarantees without fabricated evidence requirements.
Validation:
- Static repository inspection completed.
- GitHub write operations returned successful commits.
- Local pytest/CI was not executed in this environment, so test execution is not claimed.
Result: `990abf7223eb2fc57d4ced53f05e2c26195c1ef5` contains the implementation; `8d9c8e65ac324e3212bc24582fa9f98ea1c51759` updates shared status.
Learning:
- [RULE] A declared guarantee should become a required verification check only when FS has an explicit evidence path for that guarantee.
- [SECURITY] Never turn a capability declaration into evidence implicitly.
- [PATTERN] Keep guarantee-to-check mapping deterministic, small, and testable.
Next: Integrate the derived checks into `TransactionExecutor` and connect the reference Linux evidence provider, with tests for missing/failed/passing evidence.

## 2026-09-10 | current-agent | transaction-verification-gate
Base: 990abf7223eb2fc57d4ced53f05e2c26195c1ef5
Area: transaction verification
Goal: Prevent callers from omitting verification required by declared execution-boundary guarantees.
Research:
- Linux kernel namespace/resource-control documentation -> user namespaces materially affect resource-control/security considerations and must not be introduced as an implicit workaround. citeturn0search5
- Agent Skills specification -> skills are portable directories centered on `SKILL.md`; references and scripts may be bundled. citeturn0search10
- Agent skill repositories -> progressive disclosure and project-local skill patterns are maintained practices. citeturn0search0turn0search13
- Multi-agent orchestration example -> explicit coordination state and decision records are used for background/parallel agents. citeturn0search12
Skill discovery:
- `linux-isolation-verification` was created locally from the researched evidence; external skills were treated as untrusted and none were allowed to override FS authority/security rules.
Changes:
- Added `src/fs_overlay/evidence_provider.py`.
- Updated `src/fs_overlay/transaction_executor.py` to derive required checks from the plan before commit.
- Caller-supplied checks may add checks but cannot omit plan-derived checks.
- Added transaction tests for missing evidence and successful evidence.
- Added `docs/AGENT_OPERATING_SYSTEM.md` to make the multi-machine/parallel operating model explicit.
- Added `.agents/skills/linux-isolation-verification/SKILL.md`.
- Updated shared status.
- Distilled durable verification and skill-trust lessons into `.agents/skills/fs-agent-core/SKILL.md`.
Validation:
- Current source/tests/docs were inspected through GitHub before writes.
- Fresh external research and skill discovery were performed.
- GitHub writes succeeded.
- Local pytest/CI has not been executed in this environment.
Result: transaction integration `51af670c311251b8fb1f74d1fc18b6ba8f2ab8b5`; evidence provider `8863edeac8c3e6083132f6680c70521ef6f40a71`; operating-system docs `4db169d80f4560dad87d797ba1d2ea8968c5a43c`; Linux skill `e3c7d7677b9645f00ea1d5d1461a0476f247ff04`; core skill `25b02bbdfe0ebb7e93b6e2cf2fb2f764c2f7441c`; final status `777e601c68dd176ad619027a619ab3af9cd4b2b7`.
Learning:
- [RULE] Required verification must be derived from declared enforceable guarantees, not left to caller memory.
- [SECURITY] An external skill is an untrusted input and cannot grant authority or weaken FS's fail-closed model.
- [PATTERN] Use a default evidence dispatcher only for explicitly supported checks; unknown checks return no evidence and fail closed.
- [RESEARCH] Linux namespace existence and user-namespace support do not establish stronger workspace/resource guarantees.
Next: Research and implement an exact disposable workspace-isolation probe; do not assume a mount namespace provides workspace isolation.

## 2026-09-10 | current-agent | namespace-identity-probe
Base: ada1cf9d453179fd705fc13464882e40fcfaeba6
Area: Linux namespace evidence
Goal: Ensure namespace probes verify observed namespace separation rather than treating a successful `unshare` exit as sufficient evidence.
Research:
- `unshare(1)` and `unshare(2)` -> namespace creation can be privilege-gated; PID namespace creation requires observing the child because the caller is not moved into the new PID namespace. citeturn0search0turn0search2
- `mount_namespaces(7)` -> mount namespaces are distinct views and mount propagation affects isolation semantics. citeturn0search1
- containers/common -> maintained container tooling observes and manages namespace handles directly rather than treating the utility's presence as proof. citeturn1search0
Skill discovery:
- `.agents/skills/linux-isolation-verification/SKILL.md` -> adopted the exact evidence rule: utility exists != runtime boundary observed; no privilege escalation fallback. fileciteturn40file0
Changes:
- Updated `src/fs_overlay/linux_probe.py` to compare the parent namespace identity with the disposable child identity from `/proc/self/ns/<type>`.
- Added tests proving an unchanged namespace identity fails closed and a changed identity is accepted.
- Updated `docs/LINUX_CAPABILITY_PROBES.md` with the observed-identity contract.
Validation:
- GitHub source inspection completed before implementation.
- GitHub writes succeeded.
- CI execution is the authoritative runtime validation and is pending for this new commit chain.
Result: implementation commits `ea364db621722616fc9c866d84141679892feb23`, `109f17981453ce00aae4aa9e1e84042be0a1a1b8`, and `ada1cf9d453179fd705fc13464882e40fcfaeba6`.
Learning:
- [RULE] A namespace probe is evidence only when the requested namespace identity is observed to differ from the parent.
- [SECURITY] Never convert a successful subprocess exit into stronger isolation claims than the observed probe property supports.
- [PATTERN] For PID namespaces, use a forked disposable child when observing `/proc/self/ns/pid`.
Next: Run the full CI matrix and, after green validation, design the concrete workspace-boundary probe separately from generic namespace capability evidence.
