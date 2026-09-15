# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation head: `a2fbce2ffec0db8bda8c74c8c64715f3491ef3c1`
- Updated: 2026-09-15

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: Phase 3 workspace transfer materializer / authority, policy, revocation, authenticated identity, transport, journal, and recovery boundary
- goal: make any future transfer executor depend on explicit authority, durable transaction state, independently verified recovery evidence, auditable recovery decisions, policy constraints, authenticated identity, durable revocation, and an authenticated transport session
- status: CI #634 exposed a semantic regression in the reference key lifecycle adapter: RETIRED keys must remain admitted and verification-capable while being non-signing and non-reactivatable. Fixed the adapter to separate retirement non-reactivation from terminal revocation. Fresh validation is now pending.
- decision: policy, audit, identity, transport, and revocation evidence never grant host authority implicitly; source deletion remains prohibited; host filesystem mutation remains disabled
- next_step: validate the repaired head in GitHub Actions, then continue provider-boundary conformance and the AEAD boundary audit; review recovery/audit separation for remaining fail-open ordering gaps

## Latest work

- `a2fbce2ffec0db8bda8c74c8c64715f3491ef3c1` — keep retired keys verification-capable while preventing reactivation.
- `4d94cbd42fd05e33e18e58af7f2e7b28457eeef0` — attempted terminal lifecycle handling; CI exposed that retirement must remain verification-capable.
- `3e30f0e7cbf61e72b97cb8a5d909a62ba1425d9c` — refresh status after CI regression fixes.
- `091bdc1f076a37d868b33bae0965b22a50c12890` — restore production-adapter lifecycle regression expectations.
- `1f7a0e26856854f3240fc4661b8db1ba3593b713` — fix identity admission test double to implement explicit key retirement.
- `9548abe92d106341aae1e2c0f1908707a11cc9da` — add executor gate-ordering regressions proving revoked authority and invalid journal state do not touch the transport provider.
- `8f57d366a718c5ebf64d26e8bb6f4f093eac2512` — add transport regression proving provider close errors cannot mask the intended security failure.

## Validation boundary

GitHub Actions is authoritative because no local checkout/test runner is available. CI #634 on `106065e28c822c7f10ab28a987ada25231a40ba2` failed 2 lifecycle assertions across the supported OS/Python matrix: retirement incorrectly made the reference adapter report the key as not admitted and not verification-capable. Independent conformance consumers passed and all candidate crypto-provider jobs passed. The defect is fixed in `a2fbce2ffec0db8bda8c74c8c64715f3491ef3c1`; fresh validation is pending. FreeBSD native CI remains intentionally disabled and is outside the release gate.

## Current V1 position

V1 is **not** production-ready. Candidate AES-GCM qualification is behavioral evidence only. Production still requires a real audited AEAD, secure key storage/lifecycle, authenticated/encrypted transport provider, authoritative durable trust-root and identity verification, target-specific recovery evidence, and required external security review. The current Python authority/policy objects and authenticated-principal evidence are explicit contracts/provenance, not authenticated security tokens. Policy/authority digests are correlation identifiers, not authentication.

## Existing architecture boundary

Preserve fail-closed isolation, explicit authority, evidence-before-commit, no secret material in repository state, and the distinction between capability detection and granted authority. Reuse `SnapshotStore`/`MerkleDAG` for immutable content-addressed workspace state. Workspace transfer plans, journal entries, materializer preflight results, recovery/rollback evidence, policy decisions, authenticated identity evidence, transport evidence, revocation state, and audit decisions must not be presented as completed filesystem migration, recovery, rollback, or authentication.

## Next phase

1. Validate secure key storage/lifecycle conformance, including explicit ACTIVE/RETIRED/REVOKED semantics and secret-material handling, without implementing key storage in FS.
2. Audit the candidate AEAD provider boundary and retain its qualification as behavioral/non-production evidence only.
3. Add/complete cross-component conformance evidence for trust-root ordering, identity admission, live revocation, transport peer binding, and provider failure paths.
4. Keep recovery and audit evidence separate from authority issuance and host filesystem capability.
5. Only after the security-provider and recovery gates pass, consider a narrowly scoped host filesystem materializer.
