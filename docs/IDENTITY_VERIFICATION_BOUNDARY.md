# Authenticated Identity Verification Boundary

FS keeps authenticated identity separate from authority, policy, revocation, and filesystem execution.

## Evidence model

`AuthenticatedPrincipal` is immutable verification evidence containing:

- principal identity;
- issuer identity;
- node identity;
- key ID and admitted public-key fingerprint;
- the trust-root identifier used by the verifier;
- SHA-256 digest of the signed claims.

The record contains no private key, secret, credential blob, or transport session state. Constructing the record directly is not authentication and must never grant authority.

## Verification gate

A production `PrincipalVerifier` must fail closed unless all required facts are established by authoritative mechanisms:

1. issuer resolves to an admitted trust root;
2. node identity is admitted and bound to the expected public-key fingerprint;
3. key ID is admitted for that node and fingerprint;
4. key lifecycle permits verification;
5. signature verifies over the exact claims;
6. the signed claims bind the principal, issuer, node, key, fingerprint, and trust-root context represented by the returned evidence.

The verifier returns immutable evidence only after these checks succeed.

## Trust roots

`TrustRootStore` is an explicit deployment boundary. Peer discovery, DNS, configuration advertisement, or a presented fingerprint must not become a trust root merely because they were observed.

Trust-root changes are administrative security operations. Deployments must define root rotation, overlap/retirement, revocation propagation, storage protection, audit records, and recovery behavior.

## Key lifecycle

The existing `KeyLifecycle` state machine remains the deterministic reference contract: ACTIVE keys may sign and verify, RETIRED keys may verify according to retention policy, and REVOKED keys may neither sign nor verify. Key IDs cannot silently change fingerprints.

Production key state must be authoritative and durable, and must not be reconstructed from untrusted peer claims.

## Relation to policy and revocation

Authenticated identity is a prerequisite, not an authority grant. The resulting evidence must be bound to `PolicyAuthorization` before transfer authority can be issued and must remain subject to durable authority revocation.

Policy digests and authority IDs remain correlation identifiers. They are not substitutes for authentication.

## Transport boundary

Authenticated transport must bind the authenticated peer identity to the same admitted node/key facts before payload admission. Loss of authentication must fail closed. Transport encryption and credential validation remain deployment-specific provider responsibilities.

## Security boundary

This repository step defines contracts and semantic evidence only. It does not implement cryptographic verification, certificate validation, secure key storage, trust-anchor administration, authenticated transport, or a production credential system. Those require audited deployment-specific providers and external security review where required.
