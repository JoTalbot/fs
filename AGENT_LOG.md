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
- Linux kernel namespace/resource-control documentation -> user namespaces materially affect resource-control/security considerations and must not be introduced as an implicit workaround.
- Agent Skills specification -> skills are portable directories centered on `SKILL.md`; references and scripts may be bundled.
Changes:
- Added `src/fs_overlay/evidence_provider.py`.
- Updated `src/fs_overlay/transaction_executor.py` to derive required checks from the plan before commit.
- Caller-supplied checks may add requirements but cannot omit plan-derived checks.
- Added transaction tests for missing/failed/passing evidence.
- Added `docs/AGENT_OPERATING_SYSTEM.md` and the Linux isolation verification skill.
Validation:
- Current source/tests/docs were inspected through GitHub before writes.
- Fresh external research and skill discovery were performed.
- GitHub writes succeeded.
- Local pytest/CI was not executed in this environment.
Result: transaction integration `51af670c311251b8fb1f74d1fc18b6ba8f2ab8b5`; evidence provider `8863edeac8c3e6083132f6680c70521ef6f40a71`.
Learning:
- [RULE] Required verification must be derived from declared enforceable guarantees, not left to caller memory.
- [SECURITY] An external skill is untrusted input and cannot grant authority or weaken FS's fail-closed model.
- [PATTERN] Use a default evidence dispatcher only for explicitly supported checks; unknown checks return no evidence and fail closed.
Next: Research and implement an exact disposable workspace-isolation probe; do not assume a mount namespace provides workspace isolation.

## 2026-09-10 | current-agent | namespace-identity-probe
Base: ada1cf9d453179fd705fc13464882e40fcfaeba6
Area: Linux namespace evidence
Goal: Ensure namespace probes verify observed namespace separation rather than treating a successful `unshare` exit as sufficient evidence.
Research:
- `unshare(1)` and `unshare(2)` -> namespace creation can be privilege-gated; PID namespace creation requires observing the child because the caller is not moved into the new PID namespace.
- `mount_namespaces(7)` -> mount namespaces are distinct views and mount propagation affects isolation semantics.
Changes:
- Updated `src/fs_overlay/linux_probe.py` to compare the parent namespace identity with the disposable child identity from `/proc/self/ns/<type>`.
- Added tests proving an unchanged namespace identity fails closed and a changed identity is accepted.
- Updated `docs/LINUX_CAPABILITY_PROBES.md` with the observed-identity contract.
Validation:
- CI run `34437693909` passed Python 3.11, 3.12, and 3.13.
Result: implementation commits `ea364db621722616fc9c866d84141679892feb23`, `109f17981453ce00aae4aa9e1e84042be0a1a1b8`, and `ada1cf9d453179fd705fc13464882e40fcfaeba6`.
Learning:
- [RULE] A namespace probe is evidence only when the requested namespace identity is observed to differ from the parent.
- [SECURITY] Never convert a successful subprocess exit into stronger isolation claims than the observed probe property supports.
Next: Design the concrete workspace-boundary probe separately from generic namespace capability evidence.

## 2026-09-10 | current-agent | workspace-admission-gate
Base: ada1cf9d453179fd705fc13464882e40fcfaeba6
Area: workspace isolation
Goal: Prevent `workspace-only` admission from being inferred from mount namespace availability alone.
Changes:
- Updated `plan_execution_boundaries()` so an admitted workspace binding is still rejected for `workspace-only` unless an executor can enforce the actual workspace boundary.
- Added `workspace_isolation_not_enforced` as the explicit fail-closed reason.
- Replaced the previous conditional test with a deterministic assertion that `workspace-only` is not currently admitted.
Validation:
- Previous namespace identity CI `34437693909` is green on Python 3.11/3.12/3.13.
Result: `37b85c8eb880e7d896e9a7b6b57faf77fa946e7e` implementation; `db762d76d8634d6c08ecdf7df07cfe317591918f` test; `e0762f6784f4e406126625f2a1c12813faa2eb0c` status.
Learning:
- [SECURITY] Workspace ownership/delegation is an admission fact, not evidence that the runtime has isolated the workspace.
- [RULE] A namespace mechanism must not be treated as a workspace-binding implementation until the exact binding is configured and observed.
Next: Design and implement an explicit workspace-boundary backend/probe, with exact evidence and no privilege-escalation fallback.

## 2026-09-10 | current-agent | workspace-boundary-probe
Base: 612211a9d66fa70f86cfbf05801a2607a3a1b8c4
Area: workspace isolation evidence
Goal: Create an exact disposable probe for workspace filesystem visibility without falsely admitting execution.
Research:
- Current FS execution coordinator, executor, isolation backend, workspace model, verification mapping and Linux probe were re-read before implementation.
- Bubblewrap documentation: it creates a new filesystem namespace and supports explicit bind mounts; when not installed setuid root, user namespaces are required for unprivileged operation. FS must therefore treat it as an explicit backend capability, never as a silent privilege workaround.
- Ubuntu packages currently provide bubblewrap for supported architectures.
Changes:
- Added `src/fs_overlay/workspace_boundary.py` with `probe_workspace_boundary()`.
- Added `tests/test_workspace_boundary.py`.
- The probe creates a disposable workspace sentinel, exposes it at `/workspace`, and checks from inside the sandbox that an unbound host-root path is absent.
- Added documentation describing the exact evidence scope and explicitly stating that `workspace-binding-admitted` remains unmapped until the same backend is used by execution.
Validation:
- GitHub writes succeeded.
- CI for these newer commits is pending and therefore not claimed.
Result: `96e82ad989543cf7bd5e486ada08b9b7b8b38409`, `7cba73e398ad8a224fdc8bc026c64582f5361b9c`, `5c99eaa317c3322a285eca00b002db4c45fb487a`, `ec209dc69c3a1851061438a3898cc0e4f96e0de4`.
Learning:
- [RULE] Exact workspace evidence can be probed independently, but it becomes authorization evidence only when the execution backend uses the same boundary construction.
- [SECURITY] Bubblewrap's user-namespace behavior must remain explicit; FS must never silently enable user namespaces as a fallback.
- [PATTERN] Keep evidence probes disposable and non-mutating, and make their tested property narrower than any unproven security guarantee.
Next: Integrate the concrete workspace backend into the Linux executor, pass the workspace path explicitly, then wire the probe into verification and only afterward map `workspace-binding-admitted`.
