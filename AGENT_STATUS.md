# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Current commit: `6eb0686d5c82de623c64846177d2f42b6d5ca89d`
- Updated: 2026-09-14

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: failure/recovery and protocol qualification
- claimed_files: `src/fs_overlay/replication_policy.py`, `tests/test_replication_policy.py`, `AGENT_STATUS.md`, `AGENT_LOG.md`
- goal: qualify failure-domain-aware replica recovery and deterministic multi-node substrate behavior
- status: awaiting CI validation after self-correction
- decision: known unhealthy present replicas must not satisfy desired copy count or reserve their failure domain; unknown present nodes retain the existing replica-count compatibility behavior but do not reserve a failure domain
- next_step: validate the corrected policy, then continue deterministic two-node/three-node federation fixtures and explicit journal/crash boundaries

## Latest work

- `1c39e78ef5a43121bda1582f1ca26c578790733d`: corrected the replica recovery fix after CI exposed that unknown `present_on` entries are part of the existing copy-count contract.
- `6eb0686d5c82de623c64846177d2f42b6d5ca89d`: corrected regression coverage to preserve unknown-present compatibility while requiring recovery of known unhealthy replicas.
- CI #376 (`34855160140`) **failed** on the first attempt: 274 passed, 1 failed, 3 skipped, 8 deselected. The failure was an existing expectation that an unknown present node counts toward the desired copy count. No platform-specific failure occurred.
- The failing Ubuntu 3.11 log was inspected before correction; the same test logic affected the full Python matrix.
- CI #372 (`34853735052`): **18/18 jobs passed** for the prior Windows coordination fix across Ubuntu/Windows/macOS and Python 3.11/3.12/3.13, including candidate crypto-provider jobs.
- `339f867dac46126dfcd5e1333d8ab1ed37f9ccf1`: added a subprocess crash qualification immediately after durable `transaction_commit`, proving restart reconstructs committed inventory from the journal.
- `6a1e231546f7e5b24927fab44192d6300513bd7e`: qualified EventLog concurrency and append-failure recovery; CI #369 (`34853169028`) passed **18/18**.

## Current V1 position

V1 is **not** production-ready. Candidate AES-GCM qualification is behavioral evidence only. Production still requires a real audited AEAD, secure key storage/lifecycle, authenticated/encrypted transport, target-specific recovery evidence, and required external security review.

FreeBSD native CI remains intentionally disabled and outside the release gate.

## Reference production profile

The reference target is Linux with AES-256-GCM through a vetted provider, an external versioned key service, active/retired/revoked lifecycle, mutual TLS, explicit trust anchors/revocation, peer identity binding, and fail-closed handling of authentication loss, invalid credentials, replay, downgrade, and endpoint confusion. This remains a reference target, not deployment evidence.

## Existing architecture boundary

The completed foundation includes node identity/trust, signed capabilities, canonical federation envelopes, durable replay/admission state, cross-process coordination adapters, replica/self-healing primitives, deterministic negotiation, key lifecycle admission, conformance vectors/validators, MinimalInitiator, explicit production adapter contracts, EventLog recovery/concurrency qualification, and transaction crash/recovery qualification. Preserve fail-closed isolation, explicit authority, evidence-before-commit, and no secret material in repository state.

## Release-readiness boundary

The semantic V1 release gate remains blocked on deployment-specific security evidence:

1. real audited AEAD for the exact deployment;
2. secure key lifecycle storage with access control, rotation, revocation, backup/recovery and audit evidence;
3. authenticated/encrypted transport with explicit trust/revocation policy;
4. target-specific qualification and operational recovery evidence;
5. exact provider versions/configuration and external security-review evidence in `docs/PRODUCTION_QUALIFICATION_RECORD.md`.

## Next phase

- Validate corrected replica recovery semantics in the full CI matrix.
- Continue Phase 2 with remaining explicit crash points and journal recovery boundaries.
- Build deterministic two-node and three-node federation fixtures for Phase 5.
- Preserve the distinction between process-local synchronization and cross-process durable coordination.
- Keep V1 blocked until concrete production evidence exists.
