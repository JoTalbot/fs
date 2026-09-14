# Production Provider Qualification Runbook

This runbook turns the V1 security-provider gate into deployment evidence. It is intentionally conservative: a working adapter is not the same thing as a production security qualification.

## 1. AEAD provider

For each deployment target, record:

- exact provider package and version;
- build/provenance information and lockfile or equivalent;
- AES-GCM key size and configuration;
- nonce generation and uniqueness assumptions;
- maximum message/object size and invocation limits;
- authenticated-associated-data format and version;
- behavior for modified ciphertext, modified AAD, truncation and malformed envelopes;
- key rotation, retirement and revocation interaction;
- independent security review or audit evidence.

The repository's `CryptographyAESGCM` adapter is a candidate implementation only. Its tests qualify the adapter semantics, not the provider's security or the deployment's key-management controls.

## 2. Secure key storage

For every concrete `SecureKeyStore` implementation, record:

- implementation identity and version;
- trust-root and access-control model;
- stable key identifiers and fingerprints;
- creation, activation, rotation, retirement and revocation behavior;
- restart, backup and recovery behavior;
- denial behavior for unknown or revoked keys;
- audit/logging behavior and sensitive-data handling;
- independent security review appropriate to the deployment threat model.

Keys must not be placed in source control, test fixtures used by production, ordinary configuration files, or unprotected logs.

## 3. Authenticated transport

For every concrete `AuthenticatedTransport`, record:

- protocol and implementation/version;
- peer identity binding;
- certificate or trust-anchor configuration;
- hostname/service identity policy where applicable;
- revocation and expiry handling;
- handshake/authentication failure behavior;
- downgrade and algorithm-selection policy;
- protection against replay and message substitution at the transport boundary;
- independent security review appropriate to the deployment.

Loss of authentication must fail closed. Capabilities or federation metadata must never be treated as a substitute for authenticated peer identity.

## 4. Controlled AEAD test execution

The candidate AES-GCM suite is explicitly marked `crypto_provider`. It is intentionally separate from the generic dependency-free test contract until the exact crypto dependency is selected and qualified.

When qualifying the candidate in a controlled environment, install the exact pinned `cryptography` build selected for that deployment, then run:

```text
python -m pytest -m crypto_provider tests/test_production_crypto.py
```

The generic repository test command must not silently install or certify a production cryptography dependency. If the provider is unavailable, the candidate qualification is incomplete rather than skipped and reported as successful.

Preserve the exact command, dependency lock information, package/build provenance, platform, architecture, configuration and result.

## 5. Qualification execution

Run the provider-specific semantic and misuse tests on the exact artifact intended for deployment. Preserve the test command, dependency lock information, platform, architecture, configuration and result.

For production release, attach the resulting evidence to the release qualification record and reference it from `docs/V1_RELEASE_GATE.md` and `docs/PRODUCTION_SECURITY_QUALIFICATION.md`.

## 6. Release decision

V1 remains blocked when any production provider is only a candidate, lacks deployment-specific evidence, or has an unresolved security-review finding. A green generic CI matrix does not override this rule.
