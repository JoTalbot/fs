# Agent Step: Authenticated Identity Verification Boundary

Date: 2026-09-15

## Scope

This step advances the security boundary from policy/revocation claims to an explicit authenticated-identity evidence contract. It does not implement cryptography, certificate validation, secure key storage, trust administration, or authenticated network transport.

## Completed

- Added `AuthenticatedPrincipal` as immutable verification evidence containing principal, issuer, node, key, key fingerprint, trust-root, and SHA-256 claims digest context.
- Added `TrustRootStore` and `PrincipalVerifier` contracts for audited deployment-provided identity verification.
- Documented fail-closed requirements for trusted issuer resolution, admitted node/key binding, key lifecycle usability, signature validation, and exact claims binding.
- Added regression coverage proving incomplete or malformed identity evidence is rejected and that the contracts do not require secret material.
- Bound verified identity evidence to policy-bound transfer-authority issuance by requiring principal and issuer agreement with the policy authorization.
- Added regression coverage for both identity mismatch rejection and successful identity-to-policy provenance binding.
- Existing `AuthenticatedTransport` remains a separate provider boundary with explicit authentication state, bound peer identity, pre-authentication send rejection, and fail-closed lifecycle requirements.

## Security interpretation

`AuthenticatedPrincipal` is provenance evidence, not an authority token. Direct construction of the dataclass is not proof of cryptographic authentication. Authority remains gated by policy authorization and durable revocation. Policy and authority digests remain correlation identifiers, not authentication.

No private keys, credentials, session secrets, or trust-store contents are persisted in repository state.

## Remaining production qualification

1. Supply an audited concrete principal verifier with real signature and certificate/trust validation.
2. Define authoritative trust-root administration, rotation, overlap, retirement, and revocation propagation.
3. Bind the verifier to authoritative node admission and key lifecycle state.
4. Qualify secure key storage and lifecycle on each deployment target.
5. Qualify authenticated/encrypted transport, including peer identity binding and fail-closed authentication loss.
6. Bind authenticated identity provenance into revocation decisions without conflating principal revocation with individual authority revocation.
7. Produce target-specific recovery and external security-review evidence before declaring V1 production-ready.

## Validation

The latest main head is `ed35d70098cb0b04532c7440a997575277d6908d`. The workflow for the preceding implementation commit is still progressing; its completed macOS lanes are green while remaining matrix jobs are queued/in progress. GitHub Actions remains the authoritative test environment because no local checkout/test runner is available in this session.

Host filesystem mutation remains disabled.
