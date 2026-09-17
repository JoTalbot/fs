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
Base: 70470e79d2ea181351cae8acf5e2ff974e58f50
Area: repository reconnaissance and coordination state
Goal: Reconcile the shared agent state with the actual repository head before any new substantive implementation.
Research:
- Re-read `README.md`, `docs/ROADMAP.md`, `docs/V1_RELEASE_GATE.md`, `docs/CRYPTOGRAPHY_PROVIDER_STATUS.md`, `AGENT_STATUS.md`, `AGENT_LOG.md`, recent commit history, and candidate crypto-provider CI configuration.
- Confirmed `70470e79d2ea181351cae8acf5e2ff974e58f50` is the current repository head while `AGENT_STATUS.md` still referenced `d04db9a9b759be4b75681b4da420236d6ed06f90` as the latest repository head.
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

## 2026-09-16 | current-agent | dependency-review-environment-blocker
Base: ed217b349f96b4773fa2f8893b2c37f067985dd8
Area: dependency supply-chain review
Goal: Validate a narrowly scoped pull-request dependency vulnerability gate without leaving an always-failing workflow on main.
Research:
- Re-read `AGENTS.md`, `AGENT_STATUS.md`, `.github/workflows/dependency-review.yml`, `.github/workflows/ci.yml`, `pyproject.toml`, and production-security qualification docs.
- GitHub Dependency Review documentation confirms the maintained `actions/dependency-review-action@v4` workflow shape and that Dependency Graph is a prerequisite.
- OSV-Scanner documentation confirms an alternative PR workflow that compares target and feature vulnerability results and supports Python manifests/lockfiles including `pylock.toml`; it does not require GitHub Dependency Graph.
- External security skill discovery found no narrower skill that should override the local `fs-agent-core` contract.
Changes:
- Added and exercised the Dependency Review workflow on PR #12 with `fail-on-severity: high`.
- GitHub Actions run `35103492845` reached checkout and the dependency-review action with `Contents: read`, then failed with the exact environment error: `Dependency review is not supported on this repository. Please ensure that Dependency graph is enabled`.
- The same PR commit `4aa8aed2381e2e1701d1db1f97cf50fbae620ed5` passed the ordinary CI workflow `35103492850`.
- Updated `AGENT_STATUS.md` with the negative validation evidence, then removed the unsupported workflow from `main` in commit `a47308b3109ce9d89eade44aac83cb07e470eeb6` and closed PR #12 without merging it.
Validation:
- Ordinary CI on the PR head passed.
- Dependency Review workflow execution was observed and its prerequisite failure was captured from the job log; therefore no successful dependency-review validation is claimed.
Result: status synchronization `a9e286edf2d89d201ae356c30b5024e307696450`; workflow removal `a47308b3109ce9d89eade44aac83cb07e470eeb6`; PR #12 closed unmerged.
Learning:
- [FAILURE] GitHub Dependency Review cannot serve as an active gate when the repository Dependency Graph feature is disabled; leaving the workflow enabled would create a deterministic failing check for future PRs.
- [SECURITY] Negative CI evidence is still evidence: distinguish action execution from successful security-control validation.
- [RULE] When a required repository security feature is unavailable through the current administration surface, do not emulate its authority or leave a known-broken enforcement workflow enabled.
Next: Perform fresh reconnaissance before any supply-chain replacement. If an OSV-based PR gate is selected, validate it independently and keep production lockfile/toolchain decisions separate.

## 2026-09-16 | current-agent | osv-pr-gate-validation
Base: 005650886292224b3321d236b193eca9e37c0caf
Area: dependency supply-chain review / OSV PR gate
Goal: Validate and adopt a narrowly scoped OSV-based pull-request vulnerability gate without relying on GitHub Dependency Graph.
Research:
- Re-read `AGENT_STATUS.md`, `AGENTS.md`, dependency-bearing configuration, current CI conventions, and the candidate OSV workflow before the validation run.
- Current maintained OSV guidance supports recursive repository-root scanning and a PR workflow independent of GitHub Dependency Graph. Immutable action SHAs were used for the workflow.
Changes:
- Created the pinned `.github/workflows/osv-scanner.yml` candidate.
- Created reconnaissance and validation records under `docs/AGENT_STEP_2026-09-16_osv-pr-gate-*.md`.
- Removed the temporary duplicate validation workflow before PR execution.
- Opened PR #13 from `ci/osv-pr-gate-validation` into `main`.
Validation:
- OSV workflow run `35105324357` on PR #13 head `895aef52820e816b23bcf7bdd9c80e31a0480940` completed successfully; job `104824914009` reports successful setup, checkout, and dependency scan.
- Ordinary CI run `35105324326` for the same PR head completed successfully.
- PR #13 was merged successfully as `d2d8bbd11d823439c4b7be63b560215690b90c00`.
Result: OSV gate is now active on `main`; coordination status synchronized after merge.
Learning:
- [SECURITY] A real PR-triggered OSV scan provides stronger CI evidence than merely validating workflow syntax or branch presence, but it remains vulnerability-scanning evidence rather than production provenance or security certification.
- [RULE] Supply-chain CI controls must be kept separate from production lockfile/toolchain selection, SBOM completeness, provider qualification, and release security gates.
- [TOOLING] When repository Dependency Graph is unavailable, OSV-Scanner can provide a practical repository-level PR vulnerability signal without emulating Dependency Review authority.
Next: Perform fresh reconnaissance for the next non-overlapping production-boundary issue; do not repeat lifecycle persistence, transport re-authentication, release provenance, snapshot/manifest path isolation, or this OSV gate.

## 2026-09-16 | current-agent | revocation-record-schema-hardening
Base: f22ed8eba1cde27db72795379899be250ea5ef98
Area: durable authority revocation record schema
Goal: Prevent malformed persisted revocation JSON from being coerced into authoritative in-memory state.
Research:
- Re-read `AGENT_STATUS.md`, `AGENT_LOG.md`, `AGENTS.md`, canonical `fs-agent-core`, `authority_revocation.py`, its tests, and related authority/recovery boundaries.
- Fresh external research reviewed RFC 8785 and RFC 8259. Canonicalization and security guidance support parsing/validating structured input before relying on cryptographic digests, and malformed input must abort processing. NIST SP 800-57 Part 2 also emphasizes auditing key-management records.
Skill discovery:
- Repository `fs-agent-core` remained authoritative; no external skill was allowed to override the repository contract.
Changes:
- Hardened `RevocationRecord.from_line()` to require the exact persisted field set and exact JSON scalar types before constructing the record; `bool` is rejected for the integer sequence field.
- Added regressions for noncanonical field types and unknown persisted fields.
- Added `docs/AGENT_STEP_2026-09-16_revocation-record-schema-recon.md` documenting the finding and decision.
Validation:
- Validation-only PR #14 executed the real PR workflows against the implementation already on `main`.
- CI run `35106280201` (run #718) completed successfully across all 18 configured Python and candidate crypto-provider jobs.
- OSV run `35106280082` completed successfully; its dependency scan job completed successfully.
- PR #14 was intentionally not merged because its only branch change was a temporary validation marker; it remains outside `main`.
Result: implementation `c3495f181431ce3bdf22c9318dfa6d56c66cfae2`; CI and OSV validation passed for that implementation; validation-only PR #14 remains unmerged.
Learning:
- [SECURITY] Durable authoritative records need strict schema validation before digest/hash-chain verification; coercion can collapse malformed input into a valid internal representation.
- [RULE] Integrity checks do not repair schema ambiguity. Validate structure and types first, then validate the digest and chain.
- [RULE] Validation-only PR branches must never be merged when their sole purpose is to trigger CI; preserve the tested implementation independently on `main`.
Next: Synchronize `AGENT_STATUS.md` and `AGENT_LOG.md` to the validated implementation head, then perform fresh reconnaissance for the next non-overlapping production-boundary issue.

## 2026-09-16 | current-agent | secure-key-store-overwrite-hardening
Base: 98ca71af4cfa9093a8639f554b2097df30db77ee
Area: secure key-store overwrite semantics
Goal: Prevent silent replacement of protected key material under an existing key ID at the SecureKeyStore qualification boundary while preserving explicit key rotation semantics.
Research:
- Re-read `AGENTS.md`, `AGENT_STATUS.md`, canonical `fs-agent-core`, `production_adapters.py`, `adapter_conformance.py`, and `tests/test_adapter_conformance.py` from the current repository state.
- Fresh external research reviewed NIST SP 800-57 key-management guidance and OWASP secrets/cryptographic-storage guidance. These support controlled key storage and explicit lifecycle/rotation boundaries.
Skill discovery:
- External `security-review` guidance was inspected as untrusted review guidance; it specifically treats secret handling and unsafe rotation assumptions as security-review surfaces. It did not override FS's local contract.
Changes:
- Documented `SecureKeyStore.store()` as create-only for a `key_id`.
- Hardened the reusable adapter conformance harness to reject silent replacement of an existing key ID and to verify that rejected replacement leaves the original material unchanged.
- Updated the in-memory qualification store to model create-only semantics.
- Added a negative regression with an intentionally overwriting provider so the harness demonstrably rejects the unsafe behavior.
- Added `docs/AGENT_STEP_2026-09-16_secure-key-store-overwrite-recon.md` and distilled the durable rule into `fs-agent-core`.
Validation:
- Repository writes completed successfully.
- CI run `35107179255` (run #732) tested implementation head `4deb51c602f2ca12939dd52177c1b5ac5c33a8d2`. It exposed a test-fixture expectation mismatch after the new overwrite check ran first: Ubuntu 3.11 and 3.12 failed in the harness-rejection parametrization because `PermissiveKeyStore` was now correctly rejected for silent overwrite before the older empty-material expectation. The same failing job reports 488 passed and 3 skipped before the single assertion failure; independent conformance/admission checks passed. This is a regression-test expectation defect, not evidence of a runtime implementation failure.
- The failure log was inspected directly and the fix was limited to aligning that test expectation with the newly enforced ordering.
Result: implementation changes `81036be292341e8e3d93ef3a8b22e73170c399a5`, `da312fe43a65fa5d1831b2248ec40c2ae852411d`, `e0609f077dd6a671b0449d9fb3153a1f32881730`; failure analysis/fix `d98f7b0365f0b8f5696dda37e67cccb2d933af29`; research doc `436e4721f4ce055a6863717d74c1fb50f851632a`; durable skill update `4deb51c602f2ca12939dd52177c1b5ac5c33a8d2`. Validation remains pending on the corrected head.
Learning:
- [FAILURE] When strengthening a reusable conformance harness, existing negative fixtures can fail earlier on the newly added invariant; expected-failure assertions must be reviewed for the new ordering.
- [SECURITY] The first observed failure occurred in test expectations while the new security invariant itself behaved as intended; distinguish harness regressions from implementation regressions using the exact failure log.
- [VALIDATION] A failed CI run is not validation evidence for the intended final state; after a test-only correction the complete matrix must run again.
Next: Validate corrected head `d98f7b0365f0b8f5696dda37e67cccb2d933af29` through the full 18-job CI matrix. If it passes, synchronize status and retain the prior failed run as negative evidence; if it fails elsewhere, diagnose only the concrete failure.

## 2026-09-16 | current-agent | release-provenance-implementation
Base: e93a0dc465ffd41753122e7e92bd4d965867e251
Area: release artifact provenance and SBOM qualification
Goal: Establish a controlled release-shaped build path that binds exact Python artifacts to SHA-256 evidence, reproducible CycloneDX SBOM data, and GitHub artifact attestations without claiming production security certification.
Research:
- Fresh GitHub documentation confirms artifact attestations bind releasable artifacts to workflow/repository/commit/event provenance and only provide security value when verified.
- `actions/attest` supports SLSA provenance and SBOM attestations and requires `id-token`, `attestations`, and `artifact-metadata` write permissions.
- CycloneDX Python 7.3.1 supports reproducible environment SBOM generation; build tooling was kept outside the isolated target environment.
- Repository research confirmed `pyproject.toml` defines `fs-overlay` 0.1.0 with setuptools PEP 517 metadata and no mandatory runtime dependencies; ordinary CI previously had no release provenance workflow.
Changes:
- Added `.github/workflows/release-provenance.yml` with `workflow_dispatch` and `v*` tag triggers.
- Builds both sdist and wheel artifacts with pinned `build==1.3.0`.
- Generates `dist/SHA256SUMS` from the release artifacts.
- Creates an isolated target environment and generates a reproducible, validated CycloneDX JSON SBOM using `cyclonedx-bom==7.3.1`.
- Uploads the release evidence bundle with immutable `actions/upload-artifact` pinning.
- Creates signed provenance attestations for wheel and sdist and an SBOM attestation for the wheel using immutable `actions/attest` pinning.
- Corrected the initial attest action SHA before handoff; the final workflow uses `1e69f48acb82d1966a394da916b4c1698aa569d6` for `v4.2.2`.
Validation:
- Workflow file commits: `08086148aa813fa133ea41ace1bced2612f641e4`, followed by pin correction `5674db6e791b58fcc8a870c790a2df30c8810983`.
- Documentation record commit: `ebcf0583599ea29da105ee8c04837ea5d33e9805`.
- Status synchronization commit: `862f1105531ffc620ed33642da51841e89066b17`.
- The workflow intentionally does not execute on ordinary `main` pushes. No provenance/SBOM workflow success is claimed yet because this connector does not expose workflow dispatch and no release tag was created.
Result: release provenance implementation is committed and handed off for execution validation; V1 production-security blockers remain unchanged.
Learning:
- [SECURITY] Provenance is lineage evidence, not a security certification; attestation verification remains mandatory.
- [SUPPLY-CHAIN] Pin all release workflow actions to immutable upstream SHAs and retain exact artifact digests.
- [PATTERN] Generate SBOMs from an isolated environment containing the actual target package so build/SBOM tooling is not falsely represented as a runtime dependency.
- [RULE] A release-provenance workflow is not complete until it has executed and its artifact digests, SBOM and attestation verification results have been observed.
Next: Execute the release-provenance workflow through `workflow_dispatch` or a controlled `v*` tag event, inspect the resulting artifacts and attestations, and only then update the production release evidence.

## 2026-09-17 | arena-01a0af2b-fs | baseline-restoration-and-primitive-qualification
Base: 49e53b3efb144974438b9cce25fcaff7c2624ef6 (shallow clone, depth 1)
Area: repository baseline, CLI, storage/state primitives, roadmap evidence, coordination substrate
Goal: Restore an evidence-based baseline, repair real defects found by measurement, and make roadmap completion claims mechanically checkable.
Research:
- Re-read `AGENTS.md`, `AGENT_STATUS.md`, `AGENT_LOG.md`, `docs/ROADMAP.md`, `docs/ROADMAP_V1.md`, `docs/V1_RELEASE_GATE.md`, `pyproject.toml`, `.github/workflows/*`, and every module touched.
- `docs/AUTONOMOUS-DEVELOPMENT-MASTER.md`, `docs/TASK-PROTOCOL.md`, `docs/M0.md`, `docs/PRODUCT-DECISIONS.md` and `agent/state/current.yml` did not exist; they were created as extensions of the existing `AGENTS.md` protocol, not replacements (PD-006).
- Measured instead of assumed: `pkgutil.iter_modules` import census (85 modules, 1 unimportable) and `coverage.py --source=src` (85% -> 88%).
- Skill discovery: local `fs-agent-core` applies; no external skill adopted.
Changes:
- `3776407` fixed `fs_overlay/policy.py` (unclosed parenthesis made the module unimportable while CI stayed green); made `CarrierPolicy` deny lists component-wise so `.ssh/id_rsa.log` is rejected; added `tests/test_policy.py` and `tests/test_package_import_surface.py`; made crash/restart child processes export `PYTHONPATH`.
- `fc5910c` CLI `--admit` is now local configuration (`build_local_service(..., admitted=True)`) instead of an `admit` request that `GenesisService` rejects by design; malformed `--metadata` returns structured JSON with exit 2 instead of a traceback; added `tests/test_cli.py`.
- `de29ee6` added `.gitignore` (the repository had none).
- `a7e5b29` added `tests/test_state_primitives.py` (18 cases) and `tests/test_storage_primitives.py` (46 cases); added `tools/roadmap_evidence.py` + `tests/test_roadmap_evidence.py`; reconciled 33 roadmap items.
- Added `agent/state/current.yml`, `docs/TASK-PROTOCOL.md`, `docs/AUTONOMOUS-DEVELOPMENT-MASTER.md`, `docs/M0.md`, `docs/PRODUCT-DECISIONS.md`, and the step record `docs/AGENT_STEP_2026-09-17_baseline-restoration-and-primitive-qualification.md`.
Validation:
- `.venv/bin/python -m pytest`: 842 passed, 3 skipped, 14 deselected (Python 3.11.2). On the untouched tree the same command produced 3 failures and 576 passes without an installed package.
- `coverage report`: total 88%; `state_primitives.py` 63% -> 100%, `storage_engine.py` -> 94%, `cli.py` 21% -> 88%, `policy.py` -> 96%.
- `tools/roadmap_evidence.py`: 33/33 verified. `tools/independent_conformance_consumer.py` and `tools/independent_admission_conformance.py`: PASS.
- Observed CLI behaviour post-fix: `genesis ping` -> `ready: false`; `genesis ping --admit` -> `ready: true`, exit 0; malformed metadata -> structured stderr error, exit 2.
- Not observed: 18-job CI matrix on this batch (PR required); release-provenance workflow (403).
- Reproduced blocker: `gh workflow run release-provenance.yml --repo JoTalbot/fs --ref main` -> `HTTP 403 Resource not accessible by integration` on `/actions/workflows/360042142/dispatches`.
Result: four implementation commits on `arena/01a0af2b-fs` plus the coordination batch; M1 complete, M0 nearly complete, M2 blocked on human-only evidence.
Learning:
- [FAILURE] A packaged module can be unimportable while the entire matrix is green; the import surface must itself be a tested contract.
- [SECURITY] A deny list that can never match reads as protection while providing none; verify that safety branches are reachable.
- [SECURITY] Admission must never be grantable over a request transport; a CLI flag that attempts it is a broken control surface.
- [RULE] Roadmap checkboxes are claims; bind them to modules, symbols and tests and check them mechanically.
- [TOOLING] Host interpreters may reject pip installs (PEP 668); use a venv with an editable install so local runs mirror CI.
- [FAILURE] Tests that spawn interpreters must export `PYTHONPATH`, otherwise they pass in CI and fail in a source checkout.
Next: Open a PR from `arena/01a0af2b-fs` to obtain real CI/OSV evidence for this batch; then M3-01 (weakest coverage modules) and evidence reconciliation for roadmap Phases 2 and 5. Do not retry the workflow dispatch from this integration.

## 2026-09-17 | arena-01a0af2b-fs | ci-evidence-capture-for-baseline-batch
Base: 3ec5395c3d3ebde9abdecf5d1c1f963edc40274a
Area: verification evidence and coordination state
Goal: Convert the pushed baseline batch into observed CI evidence and close M0.
Research:
- `gh run list` / `gh run view` for branch `arena/01a0af2b-fs`; `gh pr view 17 --json statusCheckRollup`.
Validation:
- PR #17 head `3ec5395c3d3ebde9abdecf5d1c1f963edc40274a`: ordinary CI run `35219752637` completed **success with 18/18 jobs** (ubuntu/windows/macos x Python 3.11/3.12/3.13, tests plus crypto-provider qualification).
- OSV Vulnerability Scan run `35219752654` completed **success**.
- PR state OPEN, `mergeable: MERGEABLE`; all 19 reported checks SUCCESS.
- Local re-run before this commit: 842 passed, 3 skipped, 14 deselected; roadmap evidence 33/33.
Result: M0 exit criteria 1-11 satisfied; `agent/state/current.yml` records the run IDs, M0-07/M0-08 done, M0 done, resume point moved to M3-01.
Learning:
- [RULE] A branch push does not trigger this repository's CI (push trigger is `main` only); a pull request is the way to obtain matrix and OSV evidence for an agent batch.
- [RULE] Record run IDs against the exact head commit, so later agents do not re-request CI for an already-green head.
Next: M3-01 qualification of the weakest modules, then Phase 2 and Phase 5 roadmap evidence reconciliation.
