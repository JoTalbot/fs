# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Current commit: `010685c84c3f9eebc1f5a0cf8643919df454d970`
- Updated: 2026-09-14

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: failure/recovery and protocol qualification
- claimed_files: `src/fs_overlay/durable_coordination.py`, `tests/test_federation_state.py`, `AGENT_STATUS.md`, `AGENT_LOG.md`
- goal: make cross-process admission coordination reliable on Windows as well as POSIX
- status: validated
- decision: lock acquisition must not mutate a shared lock file through buffered writes before OS-level locking; Windows uses a retained lock file and locks byte zero directly
- next_step: continue Phase 2 with remaining explicit journal/crash boundaries and deterministic multi-node fixtures

## Latest work

- `010685c84c3f9eebc1f5a0cf8643919df454d970`: fixed Windows `FileAdmissionCoordinator` lock acquisition by removing the racy buffered sentinel write and using a retained lock file with direct byte-range locking.
- CI #372 (`34853735052`): **18/18 jobs passed** across Ubuntu/Windows/macOS and Python 3.11/3.12/3.13, including candidate crypto-provider jobs.
- CI #371 (`34853694239`) exposed a real Windows-only failure: concurrent spawned coordinators raced on `handle.flush()` while preparing the lock file, producing `PermissionError: [Errno 13] Permission denied`.
- `339f867dac46126dfcd5e1333d8ab1ed37f9ccf1`: added a subprocess crash qualification immediately after durable `transaction_commit`, proving restart reconstructs committed inventory from the journal.
- `6a1e231546f7e5b24927fab44192d6300513bd7e`: qualified EventLog concurrency and append-failure recovery; CI #369 (`34853169028`) passed **18/18**.
- `05747ab970b292f42e25ebd46531e1c79e360398`: serialized `ReplayGuard` admission with a process-local lock.
- `b2d7ebc3838807727144ba12febaabb86a734dd2`: added deterministic concurrent receiver qualification; CI #366 (`34852272343`) passed **18/18**.

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

- Continue Phase 2 with remaining explicit crash points, journal recovery boundaries, and deterministic multi-node fixtures.
- Preserve the distinction between process-local synchronization and cross-process durable coordination.
- Keep V1 blocked until concrete production evidence exists.
