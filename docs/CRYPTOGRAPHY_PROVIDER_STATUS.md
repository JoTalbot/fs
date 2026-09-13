# Cryptography provider status

## Candidate: `CryptographyAESGCM`

FS now contains an opt-in AES-256-GCM adapter backed by the Python `cryptography` package. The adapter is a concrete implementation of the `AuthenticatedEncryption` boundary and serializes envelopes as `nonce || ciphertext+tag`.

### Qualified semantics

The repository qualification tests cover:

- successful encryption/decryption;
- fresh nonce output for repeated encryption;
- associated-data binding;
- ciphertext tampering rejection;
- truncated-envelope rejection;
- strict 256-bit key-size validation.

### Release classification

**Candidate only. Not an audited production provider.**

Passing these tests demonstrates adapter semantics, not cryptographic strength, side-channel resistance, supply-chain integrity, secure key storage, nonce persistence across distributed failure domains, or deployment-specific security review.

Before this provider can satisfy the V1 production gate, record:

1. exact `cryptography` version and build provenance;
2. selected AES-GCM configuration and operational limits;
3. nonce uniqueness strategy and recovery assumptions;
4. key generation, storage, rotation, retirement, and revocation controls;
5. provider-specific misuse/negative tests in the deployment environment;
6. independent security review/audit evidence appropriate to the deployment threat model.

The provider remains opt-in and must not silently replace the integrity-only reference envelope.
