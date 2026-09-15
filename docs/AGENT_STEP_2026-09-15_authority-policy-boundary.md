# Agent step: authority policy boundary

Date: 2026-09-15  
Repository: `JoTalbot/fs`  
Branch: `main`

## Result

Added a minimal fail-closed policy contract between a future control-plane
policy decision and workspace transfer authority issuance.

The contract requires:

- explicit principal identity and issuer identity claims;
- explicit policy approval;
- exact workspace and snapshot constraints;
- source deletion permanently disabled by the transfer safety policy.

The contract does not infer authorization from filesystem capability, path
ownership, discovery, recovery evidence, or audit records.

## Security boundary

This is policy-binding evidence, not authentication. `AuthorityPrincipal` is a
claim supplied by a future authenticated control plane; this step does not
verify signatures, establish transport trust, persist revocation state, or
implement key lifecycle. Those remain production security requirements.

No host filesystem mutation was added.

## Validation

Regression coverage checks explicit approval, exact workspace/snapshot binding,
non-overridable source preservation, and required principal/issuer identity.
GitHub Actions remains authoritative for validation because no local test runner
is available in this session.

## Next

1. Bind policy authorization to the existing `TransferAuthority` issuance path.
2. Add an immutable authority identifier/provenance suitable for audit correlation.
3. Design revocation semantics that fail closed without treating audit history as authority.
4. Keep cryptographic authentication and key lifecycle as separate production security work.
