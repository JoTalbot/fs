# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation head: `efef7e47074a0cad5ed6e2631ce0496688d11d60`
- Updated: 2026-09-15

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: Phase 3 workspace transfer materializer / authority, policy, revocation, authenticated identity, transport, journal, recovery, and content-addressed workspace integrity
- goal: make any future transfer executor depend on explicit authority, durable transaction state, independently verified recovery evidence, auditable recovery decisions, policy constraints, authenticated identity, durable revocation, an authenticated transport session, and strictly validated content-addressed state
- status: snapshot object-ID integrity boundary is hardened. A CI regression exposed only an over-specific test expectation during tamper decoding: canonical object validation runs before snapshot identity verification. The test expectation was corrected without weakening fail-closed behavior.
- decision: policy, audit, identity, transport, and revocation evidence never grant host authority implicitly; source deletion remains prohibited; host filesystem mutation remains disabled; object presence remains distinct from identity and authorization
- next_step: validate the corrected head across the full CI matrix, then continue cross-component security ordering and recovery/audit separation; add code only for concrete fail-closed gaps

## Latest work

- `efef7e47074a0cad5ed6e2631ce0496688d11d60` — correct the snapshot tamper regression expectation revealed by CI.
- `dfbcc708e6f9a10b1e9e23ce779146412c006575` — document snapshot object-ID hardening step and shared coordination state.
- `42009a68fc8c3c8023830f49f21356e3800dd650` — add snapshot object-ID regression coverage.
- `9ff8ca589e792ed53b3ba8e0ecd0195735e29392` — require canonical lowercase SHA-256 object IDs at snapshot create/read boundaries.
- `ba69e16a4238a1678401d20d605d0402e15d95c2` — bind manifest lookup to the requested content identity.
- `a8ad06cdcfa370e348888053e14771ac57778c6c` — bind snapshot lookup to the requested snapshot identity.

## Validation boundary

GitHub Actions is authoritative because no local checkout/test runner is available. CI #652 (`34988832996`) failed in the test suite only because the newly added tamper-read test expected `invalid snapshot object id`, while the implementation correctly raised `snapshot identity verification failed` after canonical validation of the tampered payload changed the signed identity. Independent conformance and all candidate crypto-provider jobs passed. The test expectation was corrected in `efef7e47074a0cad5ed6e2631ce0496688d11d60`; a new CI run is required. FreeBSD native CI remains intentionally disabled and is outside the release gate.

## Current V1 position

V1 is **not** production-ready. Candidate AES-GCM qualification is behavioral evidence only. Production still requires a real audited AEAD, secure key storage/lifecycle, authenticated/encrypted transport provider, authoritative durable trust-root and identity verification, target-specific recovery evidence, and required external security review. The current Python authority/policy objects and authenticated-principal evidence are explicit contracts/provenance, not authenticated security tokens. Policy/authority digests are correlation identifiers, not authentication.

## Existing architecture boundary

Preserve fail-closed isolation, explicit authority, evidence-before-commit, no secret material in repository state, and the distinction between capability detection and granted authority. Reuse `SnapshotStore`/`MerkleDAG` for immutable content-addressed workspace state. Workspace transfer plans, journal entries, materializer preflight results, recovery/rollback evidence, policy decisions, authenticated identity evidence, transport evidence, revocation state, and audit decisions must not be presented as completed filesystem migration, recovery, rollback, or authentication.

Snapshot object IDs are schema/integrity identifiers. Their canonical SHA-256 encoding is validated independently from whether the referenced object is currently present. Availability is an execution/recovery concern and must not silently become authorization.

## Next phase

1. Continue secure key storage/lifecycle conformance, including explicit ACTIVE/RETIRED/REVOKED semantics and secret-material handling, without implementing key storage in FS.
2. Audit the candidate AEAD provider boundary and retain its qualification as behavioral/non-production evidence only.
3. Add/complete cross-component conformance evidence for trust-root ordering, identity admission, live revocation, transport peer binding, and provider failure paths.
4. Keep recovery and audit evidence separate from authority issuance and host filesystem capability.
5. Only after the security-provider and recovery gates pass, consider a narrowly scoped host filesystem materializer.
