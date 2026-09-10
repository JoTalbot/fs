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
- [SECURITY] Never convert a capability declaration into evidence implicitly.
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
- Caller-supplied checks may add but cannot omit plan-derived checks.
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
- Updated `src/fs_overlay/linux_probe.py` to compare parent namespace identity with disposable child identity.
- Added tests proving unchanged namespace identity fails closed and changed identity is accepted.
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
- Bubblewrap documentation: it creates a new filesystem namespace and supports explicit bind mounts; FS treats it as an explicit backend capability, never as a silent privilege workaround.
- Ubuntu packages currently provide bubblewrap for supported architectures.
Changes:
- Added `src/fs_overlay/workspace_boundary.py` and `tests/test_workspace_boundary.py`.
- The probe creates a disposable workspace sentinel, exposes it at `/workspace`, and checks that an unbound host-root path is absent.
- Added documentation describing the exact evidence scope.
Validation:
- GitHub writes succeeded.
- CI for those newer commits was pending at the time and was not claimed.
Result: `96e82ad989543cf7bd5e486ada08b9b7b8b38409`, `7cba73e398ad8a224fdc8bc026c64582f5361b9c`, `5c99eaa317c3322a285eca00b002db4c45fb487a`, `ec209dc69c3a1851061438a3898cc0e4f96e0de4`.
Learning:
- [RULE] Exact workspace evidence can be probed independently, but it becomes authorization evidence only when the execution backend uses the same boundary construction.
- [SECURITY] Bubblewrap user-namespace behavior must remain explicit; FS must never silently enable it as a fallback.
Next: Integrate the concrete workspace backend into the Linux executor, pass the workspace path explicitly, then wire the probe into verification.

## 2026-09-10 | current-agent | concrete-workspace-network-evidence
Base: ff35888c475287d288481144c3347aa14ca6af6f
Area: execution-scoped workspace/network semantics
Goal: Finish the concrete Linux workspace backend milestone without overstating evidence.
Research:
- Bubblewrap README/source -> new mount namespace, explicit bind mounts, and `--unshare-net` for network separation.
- Bubblewrap advisory GHSA-pxhw-h44j-8pfx -> versions before 0.12.0 are affected by sandbox-setup symlink traversal; 0.12.0 is patched.
- Bubblewrap status interface -> namespace IDs are observable backend facts.
- Linux kernel cgroup v2 -> resource control requires explicitly delegated scope.
Skill discovery:
- No external skill materially fit this Linux backend/security step; local project rules and Linux isolation workflow remained authoritative.
Changes:
- Preserved read-only/read-write workspace semantics.
- Added same-execution network namespace identity observation for `network=deny`.
- Made Bubblewrap authoritative for network admission when used by `workspace-only`.
- Routed Bubblewrap exact execution evidence through verification.
Validation:
- First CI failed stale expectations/marker names only.
- CI `34444479095` (#56) then passed Python 3.11/3.12/3.13 with 96 tests.
Result: latest implementation `6ae5d21bb6dfc46e0cf376b1e186881659b31a9a`; shared status `3eed74fb0c6183677e5797f55a4a2cb650d1784a`.
Learning:
- [SECURITY] Concrete backends must emit evidence tied to the exact execution that created the boundary.
- [RULE] Read/write workspace semantics remain explicit in backend commands.
Next: Implement delegated Linux resource controller and bounded supervisor after fresh research.

## 2026-09-10 | current-agent | resource-controller-supervisor
Base: 3eed74fb0c6183677e5797f55a4a2cb650d1784a
Area: execution runtime
Goal: Add concrete delegated Linux resource enforcement and bounded process lifecycle control without broadening authority.
Research:
- Linux kernel cgroup v2 -> delegation is the correct boundary; limits remain hierarchical.
- Python subprocess -> `communicate()` plus timeout cleanup and POSIX `start_new_session` support bounded lifecycle control.
Skill discovery:
- No external skill materially fit this step; local project security rules and Linux isolation workflow remained authoritative.
Changes:
- Added cgroup v2 backend with lease-scoped CPU, memory and PID enforcement and read-back verification.
- Added bounded supervisor with timeout cleanup, bounded restart-on-failure and resource fail-closed behavior.
- Added tests and runtime documentation.
Validation:
- CI `34444585569` (#61) exposed a stale fixture; CI `34444595490` (#62) passed with 103 tests.
- CI `34444660622` (#64) and `34444707813` (#65) passed the supervisor/documentation heads.
Result: implementation/documentation `15eeca2ced88e5c4f5a1ba8f77e5ea6ffd5d1041`.
Learning:
- [SECURITY] Resource enforcement must be scoped by explicit delegated authority and read back before reporting verified state.
- [RULE] A supervisor must never continue without a requested resource boundary.
Next: Integrate lifecycle/resource policy into the transaction/coordinator path.

## 2026-09-10 | current-agent | end-to-end-runtime
Base: 15eeca2ced88e5c4f5a1ba8f77e5ea6ffd5d1041
Area: end-to-end execution runtime
Goal: Connect admission, concrete Linux execution, supervision, resource evidence and transaction verification into one reusable path.
Research:
- Linux kernel cgroup v2 documentation -> writing a PID to `cgroup.procs` migrates the process into the delegated scope; controller behavior is hierarchical and delegation must remain contained.
- Python subprocess documentation -> `start_new_session` creates a separate POSIX session and `communicate()` is the safe pipe/timeout interaction.
- Windows Job Object documentation -> Windows provides native process-group resource limits through Job Objects; this is the next platform adapter rather than a Linux fallback.
- Bubblewrap advisory GHSA-pxhw-h44j-8pfx -> 0.12.0 remains the minimum for the current workspace backend.
Skill discovery:
- No external skill materially fit this implementation; local `fs-agent-core` and Linux isolation workflow remained authoritative.
Changes:
- Added `resource-controller` guarantee mapping and exact `resource:enforcement` evidence verification.
- Extended `ProcessResult` with resource lease identity.
- Allowed `ProcessSupervisor` to carry concrete backend evidence through its result.
- Composed optional supervision/resource enforcement into `LinuxNamespaceExecutor`.
- Added `src/fs_overlay/runtime.py` to connect plan/admission -> concrete execution -> supervision -> transaction verification -> commit.
- Added end-to-end runtime tests and updated `docs/EXECUTION_RUNTIME.md`.
Validation:
- CI `34446199320` (#77) passed Python 3.11/3.12/3.13 for resource evidence and lease identity.
- CI `34446330031` (#83) passed Python 3.11/3.12/3.13 for the end-to-end runtime tests.
- CI `34446352799` (#84) is running for the final import cleanup; it must be green before the current head is called validated.
Result: implementation head `620078fd9e740832df773221270947a4bb39fe36`; shared status update `9f9039a894c685eadc9b5863556aa0ae3b6996f5`.
Learning:
- [ARCHITECTURE] Admission, execution and verification are now connected without making admission itself evidence.
- [SECURITY] The current cgroup attach happens immediately after process creation, so the runtime must not claim enforcement before the child exists.
- [RULE] Stronger cross-platform mechanisms must be added as explicit adapters, never as Linux-specific fallbacks.
Next: After CI #84 is green, implement the Windows Job Object adapter, then a macOS service/runtime adapter and POSIX/BSD baseline before capability negotiation and versioned backend contracts.

## 2026-09-10 | current-agent | freebsd-helper-boundary
Base: e52232a9aaf340475f13295cdb29f19f2404e970
Area: FreeBSD execution boundary
Goal: Replace the conceptual Capsicum child-process path with a native helper that can safely enter capability mode before executing the workload.
Research:
- FreeBSD `cap_enter(2)` -> capability mode is process-scoped, inherited by descendants, and should be combined with rights restriction.
- FreeBSD `cap_rights_limit(2)` / `rights(4)` -> rights are reduced-only; `CAP_FEXECVE` permits `fexecve()` and requires `CAP_READ`.
- FreeBSD `fexecve(2)` -> an already-open executable descriptor can be executed without resolving its path after sandbox entry; FreeBSD recommends this pattern when constructing carefully controlled runtime environments.
Skill discovery:
- No suitable external skill found for this kernel-specific boundary; local `fs-agent-core` remained authoritative.
Changes:
- Added `native/freebsd/capsicum_exec.c`.
- Helper opens target before `cap_enter()`, limits target descriptor to `CAP_READ` + `CAP_FEXECVE`, enters and verifies capability mode, emits explicit evidence markers, then calls `fexecve()`.
- Extended `tests/test_freebsd_capsicum.py` to compile the helper with strict warnings and execute `/bin/echo` through the helper, checking both output and evidence markers.
Validation:
- GitHub commits succeeded: helper `ed7f92392df17d6162747e58e48b77e375b9fbf2`, test `b186b3b6b48f79e7def64e7b0902f846b8b9641f`.
- No FreeBSD kernel execution was available in this environment; native compilation/execution is therefore not claimed.
Result: implementation `b186b3b6b48f79e7def64e7b0902f846b8b9641f`.
Learning:
- [SECURITY] A FreeBSD sandbox helper must resolve/open required executable resources before `cap_enter()` and use descriptor-based execution afterward; path lookup after capability entry is the wrong boundary.
- [RULE] Native helper source can be tested by a real FreeBSD CI task, but source compilation is not itself native-kernel evidence.
Next: Observe the real FreeBSD CI task, then integrate the helper into a platform-specific supervisor adapter only after native evidence is green.
