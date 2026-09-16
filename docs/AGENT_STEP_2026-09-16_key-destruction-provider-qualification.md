# Agent Step — 2026-09-16 Key Destruction Provider Qualification

## Question

Does the production-provider qualification boundary explicitly require evidence for destruction/zeroization of private and symmetric key material, including retained copies, without incorrectly claiming that the reference `KeyLifecycle` destroys key bytes?

## Repository evidence

- `KeyLifecycle` models authorization/lifecycle state only; it does not own plaintext key material.
- `SecureKeyStore` is an injected provider boundary and intentionally exposes protected key storage rather than a generic in-core cryptographic module.
- Existing lifecycle and adapter conformance cover activation, rotation, retirement, revocation, fingerprint binding and rejection of silent key replacement.
- Existing `docs/AGENT_STEP_2026-09-16_key-destruction-boundary-recon.md` already concluded that adding a generic `DESTROYED` state to the reference lifecycle would invent provider authority rather than fix a demonstrated runtime defect.
- `docs/PRODUCTION_SECURITY_QUALIFICATION.md` already requires deployment-specific secure key storage evidence, but the provider runbook did not explicitly enumerate destruction/zeroization and retained copies.

## External research

- NIST SP 800-57 Part 1 Rev. 5 defines key destruction as removal of all traces of keying material and treats destruction as part of cryptographic key management. citeturn0search3turn0search5
- OWASP Key Management guidance treats destruction and zeroization as lifecycle requirements and emphasizes protected key-management mechanisms. citeturn0search1
- External security-review skills inspected during reconnaissance emphasize secret-handling, trust boundaries and evidence-first review; none was adopted as an authority over `fs-agent-core`. citeturn1search1turn1search8

## Decision

Do not add a `DESTROYED` state or memory-zeroization implementation to the FS reference lifecycle. Those operations require ownership of actual key material and deployment-specific provider semantics.

Strengthen the production qualification runbook instead. A provider must explicitly document destruction/zeroization, all retained copies and backups, metadata retention, and evidence that destruction is performed by the authoritative provider or cryptographic module. `RETIRED` and `REVOKED` remain authorization states, not proof that secret material has been destroyed.

## Change

Updated `docs/PRODUCTION_PROVIDER_RUNBOOK.md` to add a destruction qualification boundary and concrete evidence requirements for key material, copies, backups, metadata and provider-side destruction/zeroization.

## Validation boundary

This step changes documentation only. GitHub Actions validation of the resulting repository head is required before the step is marked complete. No production provider, cryptographic implementation, or destruction guarantee is claimed.

## Next safe step

After CI completes, synchronize `AGENT_STATUS.md` and continue with a non-overlapping production-boundary reconnaissance. Do not repeat the already documented transport re-authentication, trust-root binding, revocation/execution-race or key-destruction core-lifecycle questions unless new provider evidence or a concrete regression appears.
