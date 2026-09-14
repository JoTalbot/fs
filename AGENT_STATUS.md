# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Current commit: `b2d7ebc3838807727144ba12febaabb86a734dd2`
- Updated: 2026-09-14

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: failure/recovery and protocol qualification
- claimed_files: `src/fs_overlay/federation_protocol.py`, `tests/test_federation_protocol.py`, `AGENT_STATUS.md`, `AGENT_LOG.md`
- goal: make in-process federation replay admission atomic under concurrent receiver calls
- status: validated
- decision: replay protection now serializes the check-and-record critical section; concurrent callers cannot both admit the same message or sequence within one receiver instance
- next_step: continue Phase 2 with durable ordering/crash-recovery invariants; do not broaden authority or revive disabled FreeBSD CI

## Latest work

- `05747ab970b292f42e25ebd46531e1c79e360398`: serialized `ReplayGuard` admission with a process-local lock and documented the concurrency boundary.
- `b2d7ebc3838807727144ba12febaabb86a734dd2`: added deterministic concurrent receiver qualification proving exactly one admission for a duplicated message under 16 concurrent calls.
- CI #366 (`34852272343`): **18/18 jobs passed** on the replay concurrency hardening across Ubuntu/Windows/macOS and Python 3.11/3.12/3.13, including candidate crypto-provider jobs.
- `6e3862caeab313f3a3e7429c3ebe3e2df7bf5324`: fixed `FederationReconciler` to count only trusted-present replicas when calculating repair need.
- `eeafb2c2e59f872e38654649d6ff7de0f2feae22`: added regression coverage for the reconciler trust boundary.
- CI #361 (`34851345909`): **18/18 jobs passed** on the reconciler regression tests and full matrix.

## Current V1 position

V1 is **not** production-ready. Candidate AES-GCM qualification is behavioral evidence only. Production still requires a real audited AEAD, secure key storage/lifecycle, authenticated/encrypted transport, target-specific recovery evidence, and required external security review.

FreeBSD native CI remains intentionally disabled and outside the release gate.

## Reference production profile

The reference target is Linux with AES-256-GCM through a vetted provider, an external versioned key service, active/retired/revoked lifecycle, mutual TLS, explicit trust anchors/revocation, peer identity binding, and fail-closed handling of authentication loss, invalid credentials, replay, downgrade, and endpoint confusion. This remains a reference target, not deployment evidence.

## Existing architecture boundary

The completed foundation includes node identity/trust, signed capabilities, canonical federation envelopes, durable replay/admission state, cross-process coordination adapters, replica/self-healing primitives, deterministic negotiation, key lifecycle admission, conformance vectors/validators, MinimalInitiator, and explicit production adapter contracts. Preserve fail-closed isolation, explicit authority, evidence-before-commit, and no secret material in repository state.

## Release-readiness boundary

The semantic V1 release gate remains blocked on deployment-specific security evidence:

1. real audited AEAD for the exact deployment;
2. secure key lifecycle storage with access control, rotation, revocation, backup/recovery and audit evidence;
3. authenticated/encrypted transport with explicit trust/revocation policy;
4. target-specific qualification and operational recovery evidence;
5. exact provider versions/configuration and external security-review evidence in `docs/PRODUCTION_QUALIFICATION_RECORD.md`.

## Next phase

- Continue Phase 2 failure/recovery and deterministic protocol qualification with durable ordering, crash recovery, and multi-node fixtures.
- Preserve the distinction between process-local replay protection and cross-process durable admission coordination.
- Keep V1 blocked until concrete production evidence exists.
