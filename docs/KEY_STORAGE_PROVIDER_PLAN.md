# Production key-storage provider plan

FS keeps key storage behind the `SecureKeyStore` boundary. The core package must not invent a universal secret-storage implementation because deployment trust roots differ across Linux, Windows, macOS, containers, embedded systems, and external KMS deployments.

## Required provider properties

A production implementation must provide:

- opaque key material handling with no plaintext persistence by FS itself;
- stable key identifiers and authoritative fingerprints;
- explicit active/retired/revoked lifecycle states;
- controlled access to key operations;
- rotation and revocation semantics compatible with `key_lifecycle.py`;
- restart and backup/recovery behavior that does not silently change identity;
- auditable access and failure behavior;
- documented threat model and deployment-specific security review.

## Provider strategy

Prefer platform-native or externally managed roots of trust rather than storing long-lived master keys in ordinary FS configuration files.

Candidate deployment classes:

1. Linux: OS/service keyring or an external KMS/HSM integration.
2. Windows: DPAPI/Credential Manager or an external KMS/HSM integration.
3. macOS: Keychain or an external KMS/HSM integration.
4. Containers/cloud: workload identity plus an external KMS/secret manager.
5. Embedded/IoT: hardware-backed secure element where available.

These are provider classes, not certifications. A concrete implementation must be selected, versioned, tested, and security-reviewed for the actual deployment.

## V1 gate

No provider class above is considered production-qualified merely because the platform exposes it. The deployment record must contain implementation identity, configuration, lifecycle evidence, negative tests, recovery evidence, and independent security-review evidence.
