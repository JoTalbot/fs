# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Current commit: `8a5a88643ef19d0eacef0320292a4dcbafb6442e`
- Updated: 2026-09-14

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: failure/recovery and deterministic multi-node federation qualification
- claimed_files: `tests/test_federation_state.py`, `AGENT_STATUS.md`
- goal: qualify deterministic two-node/three-node durable convergence and continue explicit journal/crash boundaries
- status: multi-node fixture tests committed; CI #385 is running
- decision: independent federation nodes must derive identical durable admission indexes from the same ordered envelope stream; replay/conflicting sequence state must fail closed
- next_step: validate CI #385, fix any failures, then continue journal/crash qualification and reconciliation convergence tests

## Latest work

- `8a5a88643ef19d0eacef0320292a4dcbafb6442e`: added deterministic two-node and three-node federation-state fixtures, restart convergence coverage, and fail-closed divergent/replayed stream tests.
- CI #384 (`34855804838`) on `dea68c92d89a371c469471076a52cb188710194d`: **18/18 jobs passed** across Ubuntu/Windows/macOS and Python 3.11/3.12/3.13, including candidate crypto-provider jobs. This validates the corrected deterministic replica-policy implementation.
- CI #385 (`34856321995`) is running on `8a5a88643ef19d0eacef0320292a4dcbafb6442e`; no result is claimed until all jobs complete.
- The prior replica-policy regression was diagnosed and corrected: unknown `present_on` entries retain the existing copy-count compatibility behavior, while known unhealthy replicas no longer satisfy desired healthy copies or reserve their failure domain.
- CI #376 (`34855160140`) remains the recorded failed first attempt for that policy correction; later CI #383 validated the corrected semantics before the deterministic-selection cleanup, and #384 validates the current policy head.

## Current V1 position

V1 is **not** production-ready. Candidate AES-GCM qualification is behavioral evidence only. Production still requires a real audited AEAD, secure key storage/lifecycle, authenticated/encrypted transport, target-specific recovery evidence, and required external security review.

FreeBSD native CI remains intentionally disabled and outside the release gate.

## Reference production profile

The reference target is Linux with AES-256-GCM through a vetted provider, an external versioned key service, active/retired/revoked lifecycle, mutual TLS, explicit trust anchors/revocation, peer identity binding, and fail-closed handling of authentication loss, invalid credentials, replay, downgrade, and endpoint confusion. This remains a reference target, not deployment evidence.

## Existing architecture boundary

The completed foundation includes node identity/trust, signed capabilities, canonical federation envelopes, durable replay/admission state, cross-process coordination adapters, replica/self-healing primitives, deterministic negotiation, key lifecycle admission, conformance vectors/validators, MinimalInitiator, explicit production adapter contracts, EventLog recovery/concurrency qualification, transaction crash/recovery qualification, and failure-domain-aware replica recovery. Preserve fail-closed isolation, explicit authority, evidence-before-commit, and no secret material in repository state.

## Release-readiness boundary

The semantic V1 release gate remains blocked on deployment-specific security evidence:

1. real audited AEAD for the exact deployment;
2. secure key lifecycle storage with access control, rotation, revocation, backup/recovery and audit evidence;
3. authenticated/encrypted transport with explicit trust/revocation policy;
4. target-specific qualification and operational recovery evidence;
5. exact provider versions/configuration and external security-review evidence in `docs/PRODUCTION_QUALIFICATION_RECORD.md`.

## Next phase

- Validate CI #385 for deterministic multi-node federation fixtures.
- Continue Phase 2 with remaining explicit crash points and journal recovery boundaries.
- Extend Phase 5 with deterministic reconciliation convergence and node-loss recovery where existing abstractions support it.
- Preserve the distinction between process-local synchronization and cross-process durable coordination.
- Keep V1 blocked until concrete production evidence exists.
