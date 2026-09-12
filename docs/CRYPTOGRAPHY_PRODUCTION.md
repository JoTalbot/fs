# Production Cryptography Qualification

FS deliberately separates protocol/storage semantics from production cryptography. The storage engine exposes an `AuthenticatedEncryption` provider boundary, while the built-in HMAC envelope is explicitly integrity-only and provides no confidentiality.

## V1 rule

A deployment MUST NOT claim confidential storage unless an approved, audited AEAD provider is explicitly injected and qualified against this contract. The reference implementation does not certify a cryptographic library, algorithm, key store, certificate authority, or transport stack.

The provider MUST provide:

- authenticated encryption and decryption, not integrity-only MAC wrapping;
- authenticated associated data (AAD), so object/manifest context can be bound to ciphertext;
- failure on modified ciphertext;
- failure when AAD is changed;
- failure on malformed or truncated ciphertext;
- a documented nonce/IV strategy appropriate to the selected AEAD construction;
- a documented key lifecycle and secure key-material boundary;
- an independently reviewed/audited implementation suitable for the deployment threat model.

The FS qualification suite tests **provider semantics only**. Its test double is deliberately non-cryptographic and therefore cannot establish cryptographic strength, audit status, side-channel resistance, or secure key storage.

## Production evidence required before V1 release

1. Record the exact AEAD implementation, version, build provenance, and configuration.
2. Record the security review/audit evidence and its scope.
3. Record the nonce/IV generation, uniqueness, persistence, and recovery strategy.
4. Record where keys are generated, stored, rotated, retired, and revoked.
5. Qualify the concrete provider with the semantic tests in `tests/test_storage_crypto_boundary.py` plus provider-specific negative/misuse tests.
6. Verify authenticated transport separately. Storage AEAD does not prove peer authentication or network confidentiality.
7. Verify production key storage separately. An AEAD provider receiving plaintext keys from an insecure store does not establish a secure key lifecycle.

## Fail-closed boundary

If the production AEAD provider is absent, unqualified, unavailable, or cannot prove the required contract, FS MUST retain integrity-only/reference behavior and MUST NOT silently substitute it as confidential storage.

This document is a release qualification requirement, not a claim that the repository currently ships an audited production cryptographic provider.
