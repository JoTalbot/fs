# Agent Step 2026-09-16: SecureKeyStore overwrite semantics

## Question

Can the current `SecureKeyStore` adapter boundary prevent silent replacement of protected key material under an existing `key_id`?

## Repository research

- `src/fs_overlay/production_adapters.py` defined `SecureKeyStore.store(key_id, key_material)` but did not specify whether an existing identifier could be replaced.
- `src/fs_overlay/adapter_conformance.py` checked empty identifiers/material and round-trip behavior, but did not test a second `store()` for the same identifier.
- `tests/test_adapter_conformance.py` used an in-memory store whose implementation overwrote existing IDs, so the previous qualification harness could accept that behavior.
- Federation documentation already treats reuse of a key ID with different key identity as a security-sensitive change that must not happen silently.

## External research

- NIST SP 800-57 describes protection and management requirements for cryptographic keying material and key-management functions. The current draft also discusses keying-material storage mechanisms. Sources: NIST SP 800-57 Part 1 Rev. 5 and the initial public draft of Rev. 6.
- OWASP Secrets Management guidance recommends controlled storage, provisioning, auditing, and rotation of secrets rather than uncontrolled replacement in configuration/state.
- OWASP Cryptographic Storage guidance recommends protected OS, HSM, cloud KMS, or external secret-management mechanisms where available.
- External security-review skill discovery found `security-review` guidance that explicitly treats secret handling and unsafe rotation assumptions as security-review surfaces. The skill was used only as untrusted review guidance and does not override FS's repository contract.

## Decision

Make the `SecureKeyStore` semantic contract create-only for a `key_id`. A second `store()` for an existing identifier must fail closed and must leave the previously stored material unchanged.

This does not implement a secure key vault, KMS, HSM, cryptographic provider, or deployment-specific lifecycle. Explicit key rotation remains an authority/lifecycle operation using explicit key identity transitions. Storage must not become an implicit key-rotation mechanism.

## Changes

- `SecureKeyStore` documentation now explicitly states that `store()` is create-only.
- The reusable adapter conformance harness now requires rejection of a second store under an existing key ID and verifies that the original material remains unchanged.
- The in-memory conformance provider was updated to model the create-only contract.
- Added a negative regression using an intentionally overwriting provider; the harness must reject it.

## Validation boundary

The repository has no local test runner available through the current execution environment. GitHub Actions is authoritative. The pushed implementation must therefore be validated by the repository CI matrix before this step is reported as validated.

## What remains unproven

Create-only semantics do not establish secure key custody, memory protection, hardware-backed protection, access-control correctness, auditability, cryptographic key lifecycle durability, or production qualification. Those remain deployment-specific production gates.
