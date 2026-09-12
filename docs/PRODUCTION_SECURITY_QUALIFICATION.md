# Production security qualification

FS deliberately separates protocol semantics from deployment security mechanisms. The repository can qualify adapter behavior, but it must not label a test double or a generic library as an audited production security implementation without external evidence.

## V1 production requirements

A deployment claiming V1 production security must provide all three security providers below and retain implementation-specific evidence for the exact versions/configuration deployed.

### 1. Confidentiality provider

The `AuthenticatedEncryption` provider must be a real authenticated-encryption implementation, not an integrity-only construction.

Required evidence:

- authenticated encryption with confidentiality and integrity;
- authentication failure for modified ciphertext;
- authentication failure for modified associated data;
- explicit nonce/IV lifecycle rules appropriate to the selected algorithm;
- key-size and input-domain validation;
- documented algorithm and provider/version;
- security review and supply-chain provenance appropriate to the deployment;
- independent test vectors or interoperability evidence where available;
- no reuse of the repository's HMAC integrity envelope as a confidentiality implementation.

`tests/test_storage_crypto_boundary.py` qualifies only the semantic provider contract. Its deterministic HMAC-based double is intentionally non-cryptographic and is not production evidence.

### 2. Secure key storage

A `SecureKeyStore` production implementation must demonstrate:

- opaque key material handling outside core FS logic;
- protected-at-rest storage or an external key-management service appropriate to the threat model;
- stable key IDs and immutable identity/fingerprint binding;
- active, retired and revoked lifecycle transitions;
- access control and least privilege;
- rotation and revocation behavior across restart;
- backup/recovery behavior without silently restoring revoked authority;
- auditability of administrative key operations without exposing secret material.

### 3. Authenticated/encrypted transport

An `AuthenticatedTransport` production implementation must demonstrate:

- peer authentication before federation payload transmission;
- authenticated peer identity bound to the admitted node identity/fingerprint;
- encrypted transport for confidential payloads;
- certificate or equivalent credential validation according to deployment policy;
- explicit trust-anchor and revocation policy;
- authentication loss causes subsequent sends to fail closed;
- connection close does not leave an authenticated state usable;
- replay, downgrade and endpoint-confusion protections appropriate to the selected protocol.

## Qualification record

For each production provider, record at minimum:

1. implementation and exact version;
2. supported target platforms;
3. algorithm/protocol configuration;
4. key-management model;
5. trust-anchor/certificate policy where applicable;
6. positive and negative qualification results;
7. failure and restart behavior;
8. dependency and supply-chain review;
9. external security review, certification, or audit evidence where required by the deployment;
10. date and owner of the qualification.

## Release rule

Protocol conformance and semantic adapter tests are necessary but insufficient for production security certification. V1 remains blocked until concrete deployment providers satisfy the requirements above. No CI result can manufacture an external audit that never happened, a surprisingly common human attempt at alchemy.
