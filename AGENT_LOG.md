# FS Agent Log

Append concise, durable work records here. This is not a raw chat transcript. Each entry should let another agent understand what happened, why, what evidence exists, and what knowledge should be reused.

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

## 2026-09-15 | current-agent | recovery-authority-audit
Base: b6ee6fd1519cc454a944e7f3180e0913028e1456
Area: cross-component recovery and authority boundaries
Goal: Verify the ordering and fail-closed separation between normal executor admission, recovery evidence, rollback evidence, durable journal state, audit history, and host filesystem mutation.
Research:
- Re-read `executor_preflight.py`, `recovery_preflight.py`, `workspace_transfer_recovery.py`, `workspace_transfer_rollback.py`, `workspace_transfer_recovery_audit.py`, `workspace_transfer_journal.py`, `workspace_materializer.py`, `production_adapters.py`, `identity_verification.py`, and the governing V1/adapter/security qualification docs.
- No new fail-open defect was found in the reviewed cross-component path.
Changes:
- Added `docs/AGENT_STEP_2026-09-15_cross-component-recovery-audit.md` documenting the audit boundary and decision.
- Synchronized `AGENT_STATUS.md` to the audited head after CI completion.
Validation:
- CI #664 for `b6ee6fd1519cc454a944e7f3180e0913028e1456` completed successfully.
- Candidate provider tests remain semantic evidence only; no production audit or deployment certification is claimed.
Result: audit `b6ee6fd1519cc454a944e7f3180e0913028e1456`; status `2b8189d639f67b468c7e0577c4cfacf0ecdc9622`.
Learning:
- [SECURITY] Recovery evidence can prove a prior outcome but must never mint authority or substitute for current identity/revocation checks.
- [RULE] The reference materializer remains non-destructive until a separately qualified crash-safe host executor exists.
Next: Continue provider-specific semantic qualification and add code only for a demonstrated contract gap; keep secrets and external provider credentials out of repository state.

## 2026-09-15 | current-agent | key-lifecycle-terminal-admission
Base: d8ddb66e3b6d0d7f53f245250a8d76bff0944a78
Area: secure key lifecycle conformance
Goal: Strengthen regression coverage for terminal key admission semantics and unknown-node revocation behavior.
Research:
- Re-read `key_lifecycle.py`, `production_adapters.py`, `tests/test_key_lifecycle.py`, `tests/test_adapter_conformance.py`, and `docs/ADAPTER_CONFORMANCE.md`.
- Existing implementation already blocks re-admission after retirement/revocation; the missing evidence was explicit regression coverage for those terminal paths and for revocation requests that do not match an admitted node binding.
Changes:
- Added a regression proving a retired key cannot be re-admitted while remaining verification-capable and non-signing.
- Added a regression proving an unknown-node revoke request does not accidentally revoke the key from another node.
Validation:
- CI #667 (`34994069526`) completed successfully across the configured Ubuntu/Windows/macOS Python 3.11/3.12/3.13 matrix and candidate crypto-provider jobs.
- CI #664 (`34993046266`) for the preceding audit commit passed successfully.
Result: test `8d27a26cc07360269b035bfdca472a6863af3135`; status `8ece186001f8639be336a60025783633e6599c61`; follow-up status sync `8f1a0183b31347458d274b34d1bbc8dcb5177454`.
Learning:
- [SECURITY] Terminal lifecycle semantics need explicit negative coverage, not only positive state assertions.
- [RULE] A revocation operation must be scoped to the exact node/key binding and must not mutate unrelated authority when the requested binding is absent.
Next: Identify the next concrete provider-boundary contract gap and close it with the smallest fail-closed regression/hardening.

## 2026-09-15 | current-agent | ci667-validation-status-sync
Base: 8d27a26cc07360269b035bfdca472a6863af3135
Area: validation and agent coordination
Goal: Reconcile shared coordination state after the previously pending key-lifecycle CI completed.
Research:
- Checked GitHub Actions run `34994069526` directly after it had previously been pending.
Changes:
- Confirmed all reported jobs completed successfully.
- Updated `AGENT_STATUS.md` to distinguish latest repository head from latest validated implementation head and to record CI #667 as passed.
Validation:
- CI #667: all listed Python and candidate crypto-provider jobs succeeded.
Result: status sync `8f1a0183b31347458d274b34d1bbc8dcb5177454`.
Learning:
- [RULE] Validation claims must point to the exact implementation commit tested; documentation-only status commits do not retroactively become CI-tested implementation heads.
Next: Identify the next concrete provider-boundary contract gap and close it with the smallest fail-closed regression/hardening.

## 2026-09-15 | current-agent | provider-boundary-review
Base: d04db9a9b759be4b75681b4da420236d6ed06f90
Area: provider qualification boundary
Goal: Check whether another safe repository-level hardening step exists.
Research:
- Re-read the current coordination state, provider contracts, transport gate, adapter conformance, key lifecycle tests, and production qualification documentation.
- Fresh external research reviewed TLS 1.3 client authentication guidance and secure-software/agent-skill guidance.
Changes:
- No new repository-level contract defect was found that can be fixed without inventing deployment-specific provider authority.
- Shared status records the remaining deployment evidence blocker.
Validation:
- Existing validated implementation is `8d27a26cc07360269b035bfdca472a6863af3135`; CI #667 passed across the configured matrix.
Learning:
- [SECURITY] Do not turn an explicit provider boundary into an unaudited generic implementation merely to create additional code.
- [RULE] Stop when remaining release gates require concrete deployment evidence or independent security review rather than another core semantic change.
Next: Resume when a concrete provider/evidence package or reproducible repository-level defect appears.

## 2026-09-16 | current-agent | coordination-head-reconciliation
Base: 70470e79d2ea181351cae8dacf5e2ff974e58f50
Area: repository reconnaissance and coordination state
Goal: Reconcile the shared agent state with the actual repository head before any new substantive implementation.
Research:
- Re-read `README.md`, `docs/ROADMAP.md`, `docs/V1_RELEASE_GATE.md`, `docs/CRYPTOGRAPHY_PROVIDER_STATUS.md`, `AGENT_STATUS.md`, `AGENT_LOG.md`, recent commit history, and candidate crypto-provider CI configuration.
- Confirmed `70470e79d2ea181351cae8dacf5e2ff974e58f50` is the current repository head while `AGENT_STATUS.md` still referenced `d04db9a9b759be4b75681b4da420236d6ed06f90` as the latest repository head.
Changes:
- Updated `AGENT_STATUS.md` to record the actual repository head and preserve `8d27a26cc07360269b035bfdca472a6863af3135` as the latest validated implementation head.
Validation:
- GitHub repository metadata and commit history confirm the head transition.
- No claim is made that the documentation-only head is a new implementation validation point.
Result: status synchronization commit `3c2d684584caebe1a5bbe65d4d31ae055caabdfa`.
Learning:
- [RULE] Coordination metadata must track the actual repository head separately from the latest CI-validated implementation head.
- [SECURITY] Documentation/status synchronization must never be presented as cryptographic or runtime qualification evidence.
Next: Inspect the synchronized provider boundary for a reproducible repository-level contract defect; do not manufacture a provider implementation merely to create code churn.

## 2026-09-16 | current-agent | rotated-key-readmission-hardening
Base: 70470e79d2ea181351cae8acf5e2ff974e58f50
Area: secure key lifecycle admission
Goal: Prevent a key retired by lifecycle rotation from being used to create a new admission while preserving verification for the existing admission.
Research:
- Re-read `production_adapters.py`, `key_lifecycle.py`, `tests/test_production_adapters.py`, and provider qualification documentation.
- Identified that `KeyLifecycle.rotate()` moves the previous ACTIVE key to RETIRED, while `ReferenceKeyLifecycleAdmission.admit_key()` previously accepted any key still usable for verification. This allowed a retired key to create a new admission even though retired keys must only remain valid for verification of existing admissions.
Changes:
- Changed new admission to require `usable_for_signing()` rather than `usable_for_verification()`.
- Added a regression covering rotation, continued verification by the existing node, rejection of re-admission by another node, and admission of the new active key.
Validation:
- CI #677 (`35098613033`) for implementation head `a68fe13bc761ab42b7757d769440e6a7314d368d` completed successfully across the configured Python/platform matrix, including independent conformance and candidate crypto-provider jobs.
- The regression file was re-read from `main` after the write and confirmed intact.
Result: implementation `4f048e1a2fc0b6379616d6c0d85f44afe9e14280`; regression `a68fe13bc761ab42b7757d769440e6a7314d368d`; status synchronization pending in the follow-up coordination commit.
Learning:
- [SECURITY] Verification usability and admission eligibility are distinct lifecycle properties. A retired key may verify existing state but must not create a new authority path.
- [RULE] Lifecycle rotation must be tested as a terminal-admission boundary, not only as a status transition.
Next: Synchronize `AGENT_STATUS.md` and `AGENT_LOG.md` with the CI-validated implementation head, then resume provider-boundary reconnaissance.

## 2026-09-16 | current-agent | rotated-key-ci-status-sync
Base: a68fe13bc761ab42b7757d769440e6a7314d368d
Area: validation and agent coordination
Goal: Persist the CI-confirmed state so parallel agents see the validated implementation head immediately.
Research:
- Checked GitHub Actions run `35098613033` and its job matrix after the rotated-key admission regression completed.
- Confirmed the workflow was triggered by push of `a68fe13bc761ab42b7757d769440e6a7314d368d` and completed successfully.
Changes:
- Updated `AGENT_STATUS.md` to record `a68fe13bc761ab42b7757d769440e6a7314d368d` as both latest repository head and latest validated implementation head.
- Preserved the production-security boundary and explicit blocker list.
Validation:
- CI #677 (`35098613033`) passed across configured Ubuntu/Windows/macOS Python 3.11/3.12/3.13 jobs, independent conformance jobs, and candidate crypto-provider jobs.
Result: status synchronization `d62d5e3f575ca50b9a8af9c804486204360bad3d`.
Learning:
- [RULE] Coordination state must be synchronized immediately after CI validation so parallel agents do not work from stale implementation heads.
- [SECURITY] A successful semantic/provider-qualification CI run is not production security certification.
Next: Inspect the remaining provider-boundary state for another reproducible repository-level contract defect; if none exists, stop code changes rather than manufacture a security provider.

## 2026-09-16 | current-agent | release-evidence-reconciliation
Base: 43b2489ec1ee0c6ccc4a06611d71e055303781c8
Area: release evidence and qualification documentation
Goal: Reconcile release-gate references with the latest validated implementation without overstating security evidence.
Research:
- Re-read `docs/V1_RELEASE_GATE.md`, `docs/CRYPTOGRAPHY_PROVIDER_STATUS.md`, `docs/PRODUCTION_QUALIFICATION_RECORD.md`, and `docs/PRODUCTION_PROVIDER_RUNBOOK.md`.
- Checked repository-wide references to CI #642 and CI #667. The release gate was the stale active reference; historical agent records may legitimately retain older CI identifiers.
- Reviewed current GitHub guidance on artifact attestations. Attestations establish provenance/integrity and link artifacts to workflow, repository, commit and event, but do not certify artifact security. They are intended for releasable artifacts rather than routine test builds.
Changes:
- Updated `docs/V1_RELEASE_GATE.md` so its current CI evidence points to CI #677 (`35098613033`) and implementation head `a68fe13bc761ab42b7757d769440e6a7314d368d`.
- No production provider, key store, transport implementation, or CI attestation machinery was added.
Validation:
- Re-read the updated release gate from `main` and confirmed the audited AEAD checkbox remains unchecked and the production-security blocker remains explicit.
Result: release-gate synchronization commit `321f0e31b1e6f532fae26247a15a718a1f1d7f84`.
Learning:
- [RULE] Release evidence must identify the exact implementation head and CI run that produced it.
- [SECURITY] Provenance evidence is useful for supply-chain traceability but cannot substitute for provider security review, key custody, transport authentication, or deployment qualification.
Next: Continue with one focused production-boundary reconnaissance step; modify code only if a reproducible repository-level contract defect is found.
