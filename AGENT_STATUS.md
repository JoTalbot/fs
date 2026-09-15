# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation head: `75d868dcb3896db414eb02c13b33b248ecc4625e`
- Latest regression-test head: `32c9b52b8db60a430bcdece7542ea8b8e7973c27`
- Latest durable step record: `docs/AGENT_STEP_2026-09-15_identity-admission-conformance.md`
- Updated: 2026-09-15

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: Phase 3 workspace transfer materializer / authority, policy, revocation, and authenticated identity boundary
- goal: make any future transfer executor depend on explicit authority, durable transaction state, independently verified recovery evidence, auditable recovery decisions, policy constraints, authenticated identity, and durable revocation
- status: crash/recovery/audit qualification is end-to-end evidence-only; policy-bound authority issuance carries immutable provenance; revocation is a separate durable fail-closed registry with cross-process serialization and restart-safe reads; authenticated principal/trust-root/verifier contracts are defined; node/key admission is fail-closed; authenticated authority use requires matching principal/issuer provenance and a live durable authority-revocation check; trust-root admission now fails closed on unknown or malformed issuer anchors; key lifecycle conformance covers ACTIVE/RETIRED/REVOKED behavior
- decision: policy, audit, identity, and revocation evidence never grant host authority implicitly; source deletion remains prohibited; host filesystem mutation remains disabled
- next_step: qualify an authoritative durable trust-root/principal verifier and key-admission implementation, then authenticated transport and unified executor preflight

## Latest work

- `75d868dcb3896db414eb02c13b33b248ecc4625e` — compose optional trust-root admission with authenticated identity verification while preserving the earlier contract for non-production callers.
- `32c9b52b8db60a430bcdece7542ea8b8e7973c27` — add trust-root fail-closed and key-lifecycle ACTIVE/RETIRED/REVOKED regression evidence.
- `2c9346010ba9faaa9ae81701d12e603023b4c695` — add strict authoritative issuer trust-root admission helper.
- `1a4102ebce838fc528c9cbde7eb65e202cfe1338` — bind authenticated transfer-authority use to durable authority revocation while keeping principal/key revocation separate.
- `e48ca0b93ff59043552dc00e98b7777d6500063c` — qualify valid identity-bound authority use, principal/issuer mismatches, revoked authority rejection, and missing provenance rejection.
- `570e6bfa915ea399872a9f7fd3b391258bec34ba` — add fail-closed authenticated identity admission gate checking authoritative node/fingerprint admission, node/key/fingerprint binding, and verification lifecycle usability.

## Validation boundary

The new trust-root/lifecycle regression suite has been committed but has not yet been observed green in GitHub Actions from this session. No local checkout/test runner is available, so GitHub Actions remains authoritative. Do not treat the code as production-ready until the full supported matrix passes. FreeBSD native CI remains intentionally disabled.

## Current V1 position

V1 is **not** production-ready. Candidate AES-GCM qualification is behavioral evidence only. Production still requires a real audited AEAD, secure key storage/lifecycle, authenticated/encrypted transport, authoritative durable trust-root and identity verification, target-specific recovery evidence, and required external security review. The current Python authority/policy objects and authenticated-principal evidence are explicit contracts/provenance, not authenticated security tokens. Policy/authority digests are correlation identifiers, not authentication.

## Existing architecture boundary

Preserve fail-closed isolation, explicit authority, evidence-before-commit, no secret material in repository state, and the distinction between capability detection and granted authority. Reuse `SnapshotStore`/`MerkleDAG` for immutable content-addressed workspace state. Workspace transfer plans, journal entries, materializer preflight results, recovery/rollback evidence, policy decisions, authenticated identity evidence, revocation state, and audit decisions must not be presented as completed filesystem migration, recovery, rollback, or authentication.

## Next phase

1. Replace the contract-only trust-root/verifier boundary with an audited deployment adapter backed by an authoritative durable trust-root store, without implementing cryptography in FS.
2. Integrate authoritative node/key admission with the existing `KeyLifecycle` ACTIVE/RETIRED/REVOKED semantics and durable rotation/revocation procedures.
3. Define and qualify authenticated/encrypted transport, including peer identity binding and fail-closed authentication-loss semantics.
4. Integrate identity, policy, authority, and durable revocation checks into one executor preflight boundary without enabling host mutation.
5. Add conformance/regression evidence for identity, trust, key rotation/revocation, replay, and transport lifecycle boundaries before considering a narrowly scoped host filesystem materializer.
