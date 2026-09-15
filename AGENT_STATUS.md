# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation head: `8b05da1185c4c3f8dd50268645b22017a6046a34`
- Latest regression-test head: `91993640023b6080dc68441189c54bfd7dd39630`
- Updated: 2026-09-15

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: Phase 3 workspace transfer materializer / authority, policy, revocation, authenticated identity, and transport boundary
- goal: make any future transfer executor depend on explicit authority, durable transaction state, independently verified recovery evidence, auditable recovery decisions, policy constraints, authenticated identity, durable revocation, and an authenticated transport session
- status: crash/recovery/audit qualification is evidence-only; policy-bound authority issuance carries immutable provenance; revocation is a separate durable fail-closed registry with cross-process serialization and restart-safe reads; authenticated principal/trust-root/verifier contracts are defined; durable node/key admission is implemented; identity preflight is fail-closed; authenticated transport is now gated by peer identity, authentication state, and monotonic frame sequencing
- decision: policy, audit, identity, transport, and revocation evidence never grant host authority implicitly; source deletion remains prohibited; host filesystem mutation remains disabled
- next_step: qualify the transport gate against an injected authenticated/encrypted provider, then integrate identity + transport + policy + authority + durable revocation into one executor preflight

## Latest work

- `91993640023b6080dc68441189c54bfd7dd39630` — add transport gate conformance tests for peer binding, authentication loss, malformed frames, and replay/sequence violations.
- `8b05da1185c4c3f8dd50268645b22017a6046a34` — add fail-closed authenticated transport gate with principal peer binding and monotonic frame sequencing; cryptography remains injected.
- `932ac8fad4529b1e6c53c63e5f532d53173d7cf5` — add mandatory identity preflight conformance tests.
- `50ef4c8bf60473d6d726f3dd5b961c20cab455fb` — make the complete identity preflight fail closed for production callers.
- `75d868dcb3896db414eb02c13b33b248ecc4625e` — compose optional trust-root admission with authenticated identity verification while preserving the earlier contract for non-production callers.
- `32c9b52b8db60a430bcdece7542ea8b8e7973c27` — add trust-root fail-closed and key-lifecycle ACTIVE/RETIRED/REVOKED regression evidence.

## Validation boundary

The transport and identity changes are committed and GitHub Actions is authoritative because no local checkout/test runner is available. CI #559 is currently queued after the latest identity conformance commit; do not claim the new transport tests are green until a full supported matrix passes. FreeBSD native CI remains intentionally disabled.

## Current V1 position

V1 is **not** production-ready. Candidate AES-GCM qualification is behavioral evidence only. Production still requires a real audited AEAD, secure key storage/lifecycle, authenticated/encrypted transport provider, authoritative durable trust-root and identity verification, target-specific recovery evidence, and required external security review. The current Python authority/policy objects and authenticated-principal evidence are explicit contracts/provenance, not authenticated security tokens. Policy/authority digests are correlation identifiers, not authentication.

## Existing architecture boundary

Preserve fail-closed isolation, explicit authority, evidence-before-commit, no secret material in repository state, and the distinction between capability detection and granted authority. Reuse `SnapshotStore`/`MerkleDAG` for immutable content-addressed workspace state. Workspace transfer plans, journal entries, materializer preflight results, recovery/rollback evidence, policy decisions, authenticated identity evidence, transport evidence, revocation state, and audit decisions must not be presented as completed filesystem migration, recovery, rollback, or authentication.

## Next phase

1. Qualify the fail-closed transport gate against an injected authenticated/encrypted provider; FS must not implement cryptography.
2. Integrate authoritative node/key admission with the existing `KeyLifecycle` ACTIVE/RETIRED/REVOKED semantics and durable rotation/revocation procedures.
3. Integrate identity, authenticated transport, policy, authority, and durable revocation checks into one executor preflight boundary without enabling host mutation.
4. Add conformance/regression evidence for identity, trust, key rotation/revocation, replay, transport lifecycle, and cross-component ordering.
5. Only after those gates pass, consider a narrowly scoped host filesystem materializer.
