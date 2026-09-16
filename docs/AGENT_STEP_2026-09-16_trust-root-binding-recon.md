# Agent step: trust-root binding reconnaissance

Date: 2026-09-16
Area: authenticated identity / trust-root provider boundary
Base: `e6eeba1d9aa39603a733465757fefedd5a2e09ea`

## Question

Does the current authenticated-identity composition contain a reproducible repository-level fail-open gap in the binding between an authoritative issuer trust root and the returned `AuthenticatedPrincipal`?

## Repository research

Reviewed:

- `src/fs_overlay/identity_verification.py`
- `src/fs_overlay/identity_preflight.py`
- `src/fs_overlay/production_adapters.py`
- `tests/test_identity_verification.py`
- `docs/IDENTITY_VERIFICATION_BOUNDARY.md`
- `docs/PRODUCTION_REFERENCE_PROFILE.md`

The composition requires `TrustRootStore` and resolves the issuer before invoking the injected `PrincipalVerifier`. It then validates the returned principal against authoritative node/key admission and verification usability. The verifier contract explicitly requires signed claims to bind the principal, issuer, node, key, fingerprint, and trust-root context represented by the returned evidence.

`require_trusted_issuer()` rejects missing or malformed issuer fingerprints. The returned fingerprint is intentionally evidence of trust-root admission rather than an authentication token. The actual cryptographic binding remains the injected verifier's responsibility.

## External research

NIST SP 800-57 Part 1 Rev. 5 treats trust anchors and key-management lifecycle controls as security infrastructure and describes revocation as a mechanism whose status must be communicated to affected relying parties. This supports keeping trust-root administration and revocation as authoritative deployment boundaries rather than silently implementing them in FS core.

Source: NIST SP 800-57 Part 1 Rev. 5, https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final

## Skill discovery

The repository `fs-agent-core` skill was inspected. No additional external skill was identified as necessary for this narrow contract reconnaissance. The local skill requires fresh repository research, external research, explicit decision recording, and code changes only for demonstrated defects.

## Decision

No code change is justified in this step.

The apparent gap that the composition does not itself compare the `TrustRootStore` fingerprint with a field on `AuthenticatedPrincipal` is not a demonstrated fail-open defect: the `PrincipalVerifier` contract explicitly owns cryptographic verification and binding of signed claims to the trust-root context represented by the returned evidence. Adding a second core-side interpretation would risk duplicating deployment-specific trust semantics.

The current boundary therefore remains:

- `TrustRootStore`: authoritative trust-root admission;
- `PrincipalVerifier`: audited cryptographic verification and claim binding;
- node/key admission: authoritative identity binding and lifecycle usability;
- FS core: composition and fail-closed rejection, not trust infrastructure implementation.

## What remains unproven

This reconnaissance does not qualify any production trust-root store, certificate validation implementation, revocation propagation mechanism, secure credential store, or cryptographic verifier. Those remain deployment-specific production gates.

## Next safe step

Continue with the next provider-boundary reconnaissance and modify code only if a concrete, reproducible fail-closed contract violation is found.
