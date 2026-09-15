# Production adapter conformance

FS keeps security-sensitive deployment mechanisms behind explicit adapter contracts. This document defines the minimum semantic checks for those contracts without pretending that an in-memory test double is a production implementation.

## Contracts

- `SecureKeyStore`: key material is opaque to the core, non-empty, addressable by stable key ID, and retrievable only through the adapter.
- `AuthenticatedTransport`: authentication is an explicit lifecycle transition; federation payloads cannot be sent before peer authentication; peer identity and authentication state are observable; close terminates the authenticated state.
- `NodeAdmission`: node identity and fingerprint are authoritative admission facts. A changed fingerprint is rejected and revocation removes admission.
- `KeyAdmission`: node/key/fingerprint binding is authoritative. Key lifecycle semantics are explicit: `ACTIVE` permits signing and verification; `RETIRED` permits verification but not signing and cannot be re-admitted/reactivated; `REVOKED` permits neither and is terminal. Fingerprint changes are rejected.
- `DurableAdmissionCoordinator`: the critical section is acquired for a named resource and is released when its context exits.

## Required negative behavior

Adapter implementations must fail closed when a required security or authority fact cannot be established. At minimum, conformance tests cover:

1. unknown key cannot be loaded from a fresh key store;
2. empty key ID or key material;
3. unauthenticated transport send;
4. empty transport peer identity during authentication;
5. transport peer identity mismatch;
6. transport authentication loss after close;
7. unknown key cannot sign or verify;
8. key fingerprint change under an existing key ID;
9. retired key cannot sign;
10. retired key remains verification-capable;
11. retired key cannot be re-admitted or reactivated;
12. revoked key cannot sign or verify;
13. revoked key cannot be re-admitted or reactivated;
14. unknown node is not admitted;
15. node fingerprint change under an existing node ID;
16. revoked node is no longer admitted;
17. coordinator context releases its resource after normal exit.

The tests in `tests/test_adapter_conformance.py` use deterministic in-memory doubles solely to verify the structural and semantic contract. They do not certify cryptographic strength, secure storage, network authentication, persistence, or distributed transaction semantics.

## Production qualification boundary

A production adapter must add implementation-specific tests for its authoritative mechanism: secure key lifecycle, authenticated/encrypted transport, durable state ordering, transaction/commit semantics, crash recovery, ambiguous outcomes, access control, and operational key rotation/revocation. Those tests belong beside the adapter and must not weaken the protocol-level conformance gate.

The production key lifecycle invariant is intentionally stronger than merely observing revocation: a retired key remains usable for verification but its identity binding is terminal for admission, while a revoked key is terminal for all uses. This prevents an old credential from being silently converted back into an active authority after retirement or revocation.

The reference contracts intentionally do not select a cryptographic algorithm, certificate authority, database, consensus protocol, or network stack. Those choices remain deployment-specific and require their own security review.
