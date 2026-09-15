# Agent Step: Identity Admission Conformance Boundary

Date: 2026-09-15

## Scope

This step qualifies the semantic boundary between authenticated principal evidence and authoritative node/key admission. It does not implement cryptographic verification, certificate validation, trust-root administration, or secret-key storage.

## Required production invariant

An authenticated identity is usable for security-sensitive authority only when the externally verified evidence agrees with authoritative admission state:

1. issuer/trust-root context is established by an authoritative verifier;
2. the authenticated node is admitted with the same public-key fingerprint;
3. the authenticated key ID is admitted for that node and fingerprint;
4. key lifecycle permits verification;
5. any mismatch fails closed;
6. direct construction of evidence never bypasses these checks.

## Qualification design

The reusable adapter conformance layer already qualifies independent `NodeAdmission` and `KeyAdmission` contracts. The identity boundary therefore remains deliberately compositional rather than creating a second security authority inside FS. A deployment-specific verifier is responsible for cryptographic proof; authoritative admission providers are responsible for durable trust and lifecycle state.

The next implementation should expose a small semantic qualification helper that accepts an `AuthenticatedPrincipal`, `NodeAdmission`, and `KeyAdmission`, then verifies only the consistency relation among those facts. It must not infer trust from presented fingerprints, discovery, configuration, or the evidence object itself.

## Security interpretation

This is an admission consistency gate, not authentication. Passing the gate means only that independently authenticated evidence is consistent with currently authoritative admission state. Revocation remains a separate decision and must be checked before authority use.

## Remaining production qualification

- audited cryptographic `PrincipalVerifier`;
- authoritative durable trust-root store and rotation/revocation procedures;
- authoritative durable node/key admission implementation;
- key lifecycle integration, including ACTIVE/RETIRED/REVOKED semantics;
- authenticated/encrypted transport with peer identity binding;
- authenticated identity bound to durable authority revocation;
- target-specific recovery and external security review.

## Validation

The preceding identity-validation CI run is green across the configured matrix. This step is documentation of the next qualification boundary; no production security claim is made by this record.
