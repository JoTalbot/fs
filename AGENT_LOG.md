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
- GitHub Actions CI #376 (`34855160140`) was started for implementation `e2c1f600aee58fd9b90a546a7164499eac0091d`; it was still **in progress** when this record was written.
Result: implementation `e2c1f600aee58fd9b90a546a7164499eac0091d1`; tests `1547bd838c16861e98335f5b539e831d3b947b2a`; status `a1b67609506bf44a5a8dd863d04b55da0c57ff3f`.
Learning:
- [FAILURE] Replica recovery must distinguish healthy durable copies from nodes merely listed as present.
- [RULE] Failed or unknown placement state must never reduce the number of required healthy replicas or block failure-domain diversity.
Next: Validate CI #376, then build deterministic two-node and three-node federation fixtures and continue explicit journal/crash qualification.

## 2026-09-14 | current-agent | replica-recovery-self-correction
Base: e2c1f600aee58fd9b90a546a7164499eac0091d
Area: failure-domain-aware replica placement and recovery
Goal: Correct the recovery fix without breaking the existing `present_on` copy-count contract.
Research:
- CI #376 (`34855160140`) failed in all regular-platform suites on the pre-correction head. The first failing Ubuntu 3.11 job reported `274 passed, 1 failed, 3 skipped, 8 deselected`.
- Failure: `test_policy_prefers_new_failure_domains_deterministically` expected two new targets for `present_on={"a"}, desired_copies=3`, while the revised implementation returned three because it stopped counting the unknown present node.
Changes:
- Retained unknown `present_on` entries in the copy-count contract for backward compatibility.
- Excluded only known unhealthy present candidates from the effective present count.
- Kept failure-domain reservation based only on healthy known candidates, so an unhealthy known node cannot block recovery into another domain.
- Updated the regression to explicitly preserve unknown-present compatibility.
Validation:
- CI #376 is a confirmed failure on `e2c1f600...`; no platform-specific regression was involved.
- Corrected implementation `1c39e78ef5a43121bda1582f1ca26c578790733d`; corrected tests `6eb0686d5c82de623c64846177d2f42b6d5ca89d`.
- A new full CI run was triggered by the corrected head; validation is pending.
Learning:
- [FAILURE] A safety hardening change must preserve documented compatibility semantics unless the contract is explicitly versioned.
- [RULE] Treat unknown placement state differently from known failed state: unknown nodes may count toward legacy replica cardinality, but they must not reserve a failure domain.
Next: Validate the corrected head across the full matrix, then continue deterministic multi-node federation fixtures.

## 2026-09-14 | current-agent | multi-node-federation-fixtures
Base: dea68c92d89a371c469471076a52cb188710194d
Area: deterministic multi-node federation state convergence
Goal: Establish executable two-node and three-node fixtures proving that independent durable federation states converge on the same ordered stream and remain fail-closed on divergent or replayed entries.
Research:
- Current `federation_state.py`, `federation_protocol.py`, and `test_federation_state.py` were re-read from `main` before implementation.
- `DurableFederationState` rebuilds sender sequence high-water marks and accepted message IDs from the durable event journal, while the protocol envelope provides deterministic canonical serialization and per-sender sequencing.
Skill discovery:
- Repository `fs-agent-core` and existing federation invariants remained authoritative; no external skill was needed.
Changes:
- Added a two-node fixture consuming the same ordered four-message stream and requiring identical durable snapshots.
- Added a three-node fixture consuming a six-message multi-sender stream, then restarting one node and requiring exact snapshot convergence with its surviving peers.
- Added fail-closed coverage showing a conflicting same-sequence message and replayed message cannot alter converged state.
Validation:
- CI #384 (`34855804838`) passed 18/18 on the preceding replica-policy head.
- CI #385 (`34856321995`) was triggered by this fixture commit and was still running when this record was written.
Result: implementation/tests `8a5a88643ef19d0eacef0320292a4dcbafb6442e`.
Learning:
- [ARCHITECTURE] Multi-node convergence is currently qualified at the durable admission-index boundary, not as a network transport simulation.
- [RULE] Identical ordered protocol streams must produce identical sender high-water marks and accepted-message sets after restart.
- [SECURITY] Divergent sequence state and replay attempts must be rejected without mutating durable admission state.
Next: Validate CI #385, then continue explicit journal/crash boundaries and deterministic reconciliation/node-loss convergence where existing abstractions support it.

## 2026-09-14 | current-agent | replica-policy-test-correction
Base: 8a5a88643ef19d0eacef0320292a4dcbafb6442e
Area: deterministic replica placement qualification
Goal: Remove a false regression failure without weakening the placement policy.
Research:
- CI #389 (`34856529766`) failed on all regular-platform Python jobs at `test_policy_is_invariant_to_candidate_input_order`.
- The assertion expected `("b", "c")` while the policy correctly returned `("b", "c", "d")` because `a` is a known unhealthy present node and therefore cannot count toward the desired three healthy copies.
- Candidate crypto-provider jobs in the same CI run passed.
Changes:
- Corrected the deterministic-order regression expectation to `("b", "c", "d")` and retained the reversed-input equality assertion.
- Updated shared status to record the exact failure and correction.
Validation:
- CI #389 is a confirmed deterministic test-expectation failure, not a platform-specific implementation failure.
- Corrected test commit: `89ce7491752719f8cca3a16954fd3a5451420ed4`.
Result: `89ce7491752719f8cca3a16954fd3a5451420ed4`.
Learning:
- [FAILURE] A recovery test must encode the semantic replica-count contract, not an obsolete expected tuple copied from the pre-failure-domain behavior.
- [RULE] When a known present replica is unhealthy, desired healthy copy count must be satisfied from eligible healthy targets; input-order invariance must compare equivalent policy outputs rather than constrain the cardinality incorrectly.
Next: validate the corrected test, then continue journal/crash and reconciliation/node-loss qualification.

## 2026-09-14 | current-agent | transaction-commit-marker-failure
Base: f9590e52e6e98c5d510d1a5a643c27af89b68fcc
Area: durable transaction publication boundary
Goal: Prove that failure to append the durable transaction commit marker cannot publish staged objects after restart.
Research:
- `StorageTransaction.commit()` publishes inventory only after `transaction_commit` is durably appended; recovery publishes staged records only when that marker is replayed.
- Existing crash qualification covered process termination before the marker and after the marker, but not an injected append failure at the marker boundary.
Changes:
- Added `tests/test_storage_transaction_commit_failure.py` with an injected `transaction_commit` append failure.
- Verified the live transaction keeps an empty inventory after the failure, while restart also keeps staged data unpublished and can still verify the immutable object bytes.
Validation:
- New test is committed; full CI for the new head is pending.
- Preceding CI #393 (`34857239652`) passed **18/18 jobs** on `f9590e52e6e98c5d510d1a5a643c27af89b68fcc`.
Result: `cfdb5c32205344e08cdf1a1f82e15ceefac90a05`; status sync `2d0d555577a0785ac5b4c65eed2abe31b78e1b0f`.
Learning:
- [FAILURE] A durable publication boundary must be qualified not only for process crashes but also for synchronous persistence errors exactly at the commit marker.
- [RULE] Immutable staged bytes may survive a failed transaction, but inventory visibility must remain controlled exclusively by the durable commit marker.
Next: Validate the new commit across the full matrix, then continue deterministic reconciliation/node-loss recovery qualification.

## 2026-09-14 | current-agent | trust-filter-at-read-time
Base: cad8aae1644d5485d42ae0a002124b4f8f66205f
Area: federation trust boundary and deterministic reconciliation
Goal: Prevent retained directory observations from remaining actionable after trust is withdrawn or expires.
Research:
- `FederationDirectory.observe()` checked trust at observation time, but `available()` returned retained advertisements without rechecking current trust.
- `FederationReconciler.plan_repairs()` consumes `available()`, so a node withdrawn after observation could remain a replication source.
Changes:
- Changed `FederationDirectory.available()` to revalidate `TrustStore.admit()` at read time.
- Added regression coverage for trust disablement, expiry at a precise timestamp, and reconciliation refusing a disabled source.
Validation:
- CI #396 (`34858177089`) passed **18/18 jobs** on the preceding transaction commit-marker qualification head `cad8aae1644d5485d42ae0a002124b4f8f66205f`.
- Fresh CI for the trust-filter head is pending.
Result: implementation `e7d54da4587135510a79a54eccd15dfff59a0df8`; tests `bb0e8bd45c097b465eb018518406c5e60ba29300`; status `ef721b82f9d6e63de7519536fe52a6e292a6da9b`.
Learning:
- [SECURITY] Trust is current authority, not a one-time admission event. Cached observations must not outlive revocation or expiry.
- [RULE] Federation read paths must revalidate trust before making an identity actionable.
Next: Validate the fresh head across the full matrix, then continue deterministic node-loss/reconciliation and journal recovery qualification.
