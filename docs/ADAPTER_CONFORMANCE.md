# Production adapter conformance

FS keeps security-sensitive deployment mechanisms behind explicit adapter contracts. This document defines the minimum semantic checks for those contracts without pretending that an in-memory test double is a production implementation.

## Contracts

- `SecureKeyStore`: key material is opaque to the core, non-empty, addressable by stable key ID, and retrievable only through the adapter.
- `AuthenticatedTransport`: federation payloads cannot be sent before peer authentication; peer identity and authentication state are observable; close terminates the authenticated state.
- `NodeAdmission`: node identity and fingerprint are authoritative admission facts. A changed fingerprint is rejected and revocation removes admission.
- `KeyAdmission`: node/key/fingerprint binding is authoritative. Fingerprint changes, revoked keys, and signing/verifying after revocation are rejected.
- `DurableAdmissionCoordinator`: the critical section is acquired for a named resource and is released when its context exits.

## Required negative behavior

Adapter implementations must fail closed when a required security or authority fact cannot be established. At minimum, conformance tests cover:

1. empty key material;
2. unauthenticated transport send;
3. transport authentication loss after close;
4. key fingerprint change under an existing key ID;
5. revoked key cannot sign or verify;
6. node fingerprint change under an existing node ID;
7. revoked node is no longer admitted;
8. coordinator context releases its resource after normal exit.

The tests in `tests/test_adapter_conformance.py` use deterministic in-memory doubles solely to verify the structural and semantic contract. They do not certify cryptographic strength, secure storage, network authentication, persistence, or distributed transaction semantics.

## Production qualification boundary

A production adapter must add implementation-specific tests for its authoritative mechanism: secure key lifecycle, authenticated/encrypted transport, durable state ordering, transaction/commit semantics, crash recovery, ambiguous outcomes, access control, and operational key rotation/revocation. Those tests belong beside the adapter and must not weaken the protocol-level conformance gate.

The reference contracts intentionally do not select a cryptographic algorithm, certificate authority, database, consensus protocol, or network stack. Those choices remain deployment-specific and require their own security review.
