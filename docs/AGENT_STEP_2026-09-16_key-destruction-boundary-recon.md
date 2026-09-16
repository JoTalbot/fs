# Key Destruction Boundary Reconnaissance — 2026-09-16

## Question

Does the current key lifecycle contain a reproducible repository-level fail-open defect because it models ACTIVE, RETIRED and REVOKED states without a DESTROYED/zeroization operation?

## Repository evidence

Reviewed current `main` state and searched lifecycle, admission, federation and production-boundary references:

- `src/fs_overlay/key_lifecycle.py` defines the reference lifecycle as `ACTIVE`, `RETIRED`, and `REVOKED`.
- `ACTIVE` keys may sign and verify; `RETIRED` keys remain verification-capable; `REVOKED` keys cannot sign or verify.
- Rotation retires the previous active key and refuses silent fingerprint replacement.
- `ReferenceKeyLifecycleAdmission` is explicitly a non-durable semantic adapter. It does not own production key material.
- Existing tests cover rotation, retirement, revocation, reactivation rejection, fingerprint binding, and terminal verification/signing behavior.
- Existing project documentation explicitly treats the lifecycle as a state contract rather than a secure key store. Production key custody and lifecycle remain injected deployment responsibilities.
- The repository has already audited the create-only `SecureKeyStore` contract; adding a second key-destruction implementation inside FS core would cross the same deployment/provider boundary.

## External research

- NIST SP 800-57 Part 1 Rev. 5 describes key-management phases including a destroyed phase, while retaining key metadata for accountability where required. It treats generation, storage, use, revocation, destruction and related lifecycle functions as part of key management. citeturn0search37turn0search4
- NIST's key-management glossary likewise defines key management as handling cryptographic keys through their lifecycle, including destruction. citeturn0search2
- OWASP Key Management guidance recommends explicit lifecycle management, secure storage, compromise recovery, revocation and destruction/zeroization practices. citeturn0search0
- OWASP Cryptographic Storage guidance recommends dedicated key-management systems or protected platform mechanisms where available and explicitly separates key lifecycle/rotation from ordinary application storage. citeturn0search1
- No external Agent Skill was found that should override the repository's `fs-agent-core` contract for this provider-boundary question. External security/recovery skills remain methodology only.

## Decision

No current fail-open defect was reproduced.

The absence of a `DESTROYED` state in the reference `KeyLifecycle` is intentional within the current architecture: the object is a deterministic lifecycle/admission contract, not a cryptographic module or secure key store. A real destroyed/zeroized state requires control over actual key material, memory handling, provider semantics, audit/retention policy, backups and recovery. Implementing those concerns generically in FS core would create an unaudited security provider rather than close a demonstrated repository defect.

`REVOKED` therefore remains the terminal **authorization/use** state exposed by the reference lifecycle, while actual key destruction remains a production key-management responsibility. Production qualification must document how revoked/retired key material transitions to destruction, what metadata is retained, how backups/copies are handled, and what evidence proves completion.

## Remaining evidence gap

The V1 production blocker should continue to require concrete provider evidence for key custody and lifecycle, including revocation, rotation, retention/decryption requirements for retired material, destruction/zeroization policy, backup copies, audit/accountability and compromise recovery. Semantic lifecycle tests cannot certify those deployment properties.

## Result

No runtime implementation change is justified by this reconnaissance. Preserve the provider boundary and avoid adding a speculative `DESTROYED` state to the core reference object without a concrete executor/provider contract that owns real key material.

## Next safe step

Continue with a fresh reconnaissance of another non-overlapping production boundary. If a concrete provider implementation is later selected, qualify its destruction/zeroization semantics at that provider boundary rather than pretending the in-memory lifecycle object destroyed bytes it never owned.