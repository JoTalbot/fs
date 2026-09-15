# Agent Step: Identity Admission and Authority Revocation Conformance

Date: 2026-09-15

## Scope

This step qualifies the semantic boundary between authenticated principal evidence, authoritative node/key admission, and durable revocation of one explicit transfer authority. It does not implement cryptographic verification, certificate validation, trust-root administration, secret-key storage, or authenticated transport.

## Required production invariant

An authenticated identity is usable for security-sensitive authority only when the externally verified evidence agrees with authoritative admission state and the specific authority remains unrevoked:

1. issuer/trust-root context is established by an authoritative verifier;
2. the authenticated node is admitted with the same public-key fingerprint;
3. the authenticated key ID is admitted for that node and fingerprint;
4. key lifecycle permits verification;
5. policy binds the authenticated principal/issuer to the exact transfer authority;
6. the authority has a durable `authority_id` provenance identifier;
7. the durable authority revocation registry confirms that identifier is not revoked;
8. any mismatch or missing security provenance fails closed;
9. direct construction of evidence never bypasses these checks.

## Qualification design

The reusable adapter conformance layer qualifies independent `NodeAdmission` and `KeyAdmission` contracts. The identity boundary therefore remains deliberately compositional rather than creating a second security authority inside FS. A deployment-specific verifier is responsible for cryptographic proof; authoritative admission providers are responsible for durable trust and lifecycle state.

`validate_authenticated_principal_admission(...)` in `production_adapters.py` checks only consistency among authenticated evidence and authoritative node/key admission state: node/fingerprint admission, node/key/fingerprint admission, and verification lifecycle usability. It fails closed with `PermissionError` on every mismatch.

`validate_authenticated_transfer_authority(...)` in `workspace_transfer_authority.py` now composes the next boundary. It requires an authority with immutable policy provenance, requires the authenticated principal and issuer to match that provenance, and checks `AuthorityRevocationRegistry.is_revoked(...)` immediately before authority use. It never authenticates the evidence, never grants filesystem capability, and never treats principal/key revocation as equivalent to revoking one transfer authority.

## Security interpretation

The two revocation domains remain separate:

- **Principal/key revocation** belongs to authoritative identity admission and key lifecycle. It determines whether new authenticated evidence is usable.
- **Authority revocation** belongs to `AuthorityRevocationRegistry`. It can invalidate one already-issued transfer authority without changing the identity's global lifecycle state.

The composed gate therefore prevents a revoked transfer authority from being reused while preserving the independent identity lifecycle boundary.

## Regression coverage

`tests/test_identity_verification.py` qualifies:

- consistent authenticated principal admission;
- unknown or mismatched node admission;
- mismatched node/key/fingerprint admission;
- verification lifecycle rejection;
- runtime structural conformance of `NodeAdmission` and `KeyAdmission`.

`tests/test_workspace_transfer_authority.py` now qualifies:

- valid authenticated authority use before revocation;
- principal mismatch rejection;
- issuer mismatch rejection;
- durable authority revocation rejection;
- rejection of an authority without authenticated provenance.

## Remaining production qualification

- audited cryptographic `PrincipalVerifier`;
- authoritative durable trust-root store and rotation/revocation procedures;
- authoritative durable node/key admission implementation;
- key lifecycle integration, including ACTIVE/RETIRED/REVOKED semantics;
- authenticated/encrypted transport with peer identity binding and fail-closed authentication loss;
- target-specific recovery and external security review;
- end-to-end integration of all these boundaries into a production executor before any host filesystem mutation is enabled.

## Validation

The identity admission and authority-revocation negative paths are covered by the repository test suite. GitHub Actions remains authoritative for the full release matrix. No production security claim is made by this record.
