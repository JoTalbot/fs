# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation head: `1a4102ebce838fc528c9cbde7eb65e202cfe1338`
- Latest regression-test head: `e48ca0b93ff59043552dc00e98b7777d6500063c`
- Latest durable step record: `docs/AGENT_STEP_2026-09-15_identity-admission-conformance.md`
- Updated: 2026-09-15

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: Phase 3 workspace transfer materializer / authority, policy, revocation, and authenticated identity boundary
- goal: make any future transfer executor depend on explicit authority, durable transaction state, independently verified recovery evidence, auditable recovery decisions, policy constraints, authenticated identity, and durable revocation
- status: crash/recovery/audit qualification is end-to-end evidence-only; policy-bound authority issuance carries immutable provenance; revocation is a separate durable fail-closed registry with cross-process serialization and restart-safe reads; authenticated principal/trust-root/verifier contracts are defined; node/key admission is fail-closed; authenticated authority use now requires matching principal/issuer provenance and a live durable authority-revocation check; SHA-256 digest fields are validated for strict hexadecimal encoding
- decision: policy, audit, identity, and revocation evidence never grant host authority implicitly; source deletion remains prohibited; host filesystem mutation remains disabled
- next_step: qualify authoritative trust-root/principal verification and key lifecycle integration, then authenticated transport and end-to-end executor preflight

## Latest work

- `1a4102ebce838fc528c9cbde7eb65e202cfe1338` — bind authenticated transfer-authority use to durable authority revocation while keeping principal/key revocation separate.
- `e48ca0b93ff59043552dc00e98b7777d6500063c` — qualify valid identity-bound authority use, principal/issuer mismatches, revoked authority rejection, and missing provenance rejection.
- `e3c965217675acfd0a617678e5685e27c6a5c71d` — record the identity admission plus authority-revocation qualification boundary and remaining production requirements.
- `570e6bfa915ea399872a9f7fd3b391258bec34ba` — add fail-closed authenticated identity admission gate checking authoritative node/fingerprint admission, node/key/fingerprint binding, and verification lifecycle usability.
- `d179b883d1ec6f1a4b3c80dea6dc95c35f1f1200` — qualify identity admission success and fail-closed mismatch/revoked-key regression paths.
- `f3e61eb7e21056d7b7b9eba872371578b993c770` — bind TransferAuthority issuance to PolicyAuthorization and add immutable principal/issuer, policy digest, and authority correlation identifiers.
- `4942967ea6cbf592d328fe27ecf3a1375ec8da33` — add durable fail-closed authority revocation registry.
- `58f8d1b98d4d475c1b0135e6d781bdc72eac41aa` — harden revocation concurrency and restart-safe reads with cross-process OS locking and durable refresh.
- `72f816502e6db7800786d2680ec04846f304afe7` — qualify concurrent revocation writers with a multiprocessing regression test.
- `46dc5ccf44818143b541da4dc71b0849229f376c` — define authenticated principal/trust-root/verifier contracts and bind authenticated provenance to policy-bound authority issuance.
- `cd9f3a5937bbc6e996e8288f723353c13791c574` — qualify strict authenticated identity digest encoding and reject non-hex SHA-256 evidence.

## Validation boundary

CI run `#539` (`34958184443`) for the composed authenticated-principal verification tests is in progress; completed jobs observed so far are green, with the remaining Windows/macOS jobs still running or queued. The subsequent implementation/test/doc status commits have triggered the next CI run and require its full matrix result. No local checkout/test runner is available in this session, so GitHub Actions remains authoritative. No host filesystem mutation is implemented.

## Current V1 position

V1 is **not** production-ready. Candidate AES-GCM qualification is behavioral evidence only. Production still requires a real audited AEAD, secure key storage/lifecycle, authenticated/encrypted transport, authoritative trust-root and identity verification, target-specific recovery evidence, and required external security review. The current Python authority/policy objects and authenticated-principal evidence are explicit contracts/provenance, not authenticated security tokens. Policy/authority digests are correlation identifiers, not authentication.

FreeBSD native CI remains intentionally disabled and outside the release gate.

## Existing architecture boundary

Preserve fail-closed isolation, explicit authority, evidence-before-commit, no secret material in repository state, and the distinction between capability detection and granted authority. Reuse `SnapshotStore`/`MerkleDAG` for immutable content-addressed workspace state. Workspace transfer plans, journal entries, materializer preflight results, recovery/rollback evidence, policy decisions, authenticated identity evidence, revocation state, and audit decisions must not be presented as completed filesystem migration, recovery, rollback, or authentication.

## Next phase

1. Qualify an authoritative `PrincipalVerifier` against trust-root, node admission, key admission, and ACTIVE/RETIRED/REVOKED lifecycle state without implementing crypto in FS.
2. Define and qualify authenticated/encrypted transport, including peer identity binding and fail-closed authentication-loss semantics.
3. Integrate identity, policy, authority, and durable revocation checks into one executor preflight boundary without enabling host mutation.
4. Add conformance/regression evidence for identity, trust, key rotation/revocation, replay, and transport lifecycle boundaries.
5. Only after authority, policy, crash, rollback, authentication, and revocation qualification, consider a narrowly scoped host filesystem materializer.
