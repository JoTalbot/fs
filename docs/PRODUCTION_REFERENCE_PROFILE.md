# Production Security Reference Profile

This document defines a concrete **reference deployment profile** for the production-adapter qualification work. It is an implementation target and evidence checklist, not a statement that the profile is already deployed or audited.

## Scope

The profile targets a Linux deployment of FS where federation traffic crosses an untrusted network and application data requires confidentiality, integrity, authenticated peers, controlled key lifecycle, and fail-closed recovery.

The profile deliberately keeps security mechanisms outside the FS protocol core. The existing `SecureKeyStore` and `AuthenticatedTransport` contracts remain the integration boundaries.

## Reference choices

| Boundary | Reference choice | Qualification boundary |
| --- | --- | --- |
| Confidentiality | AES-256-GCM through a vetted provider | Exact provider version, build provenance, configuration and security review must be recorded |
| Key storage | External Vault Transit-style key service | Application receives opaque key references/ciphertext operations, not a plaintext key file |
| Key lifecycle | Versioned key generations with explicit active/retired/revoked states | Rotation, restart, recovery and revocation must be exercised against the real deployment |
| Federation transport | TLS with mutual peer authentication | Peer certificate identity must bind to the admitted FS node identity/fingerprint |
| Trust | Explicit deployment trust anchors | Discovery must never create trust implicitly |
| Revocation | Explicit certificate/key revocation policy | Revocation must fail closed for new authentication/signing operations |

## 1. Key-management profile

The reference key service should expose stable logical key IDs and versioned cryptographic material while keeping plaintext key material outside FS application storage.

Required controls:

1. FS is granted only the minimum operations required for its role.
2. Key IDs are stable, non-secret identifiers.
3. Active and retired versions remain distinguishable.
4. Rotation creates a new encryption version without immediately destroying the ability to decrypt data that is still inside the migration window.
5. The deployment defines an explicit point after which an old version is no longer accepted for decryption.
6. Revocation is authoritative and survives process restart.
7. Backups cannot silently restore revoked authority.
8. Administrative key operations are auditable without recording secret material.
9. No plaintext key is committed to source control, ordinary configuration, logs, or this repository.

### Migration rule

During rotation, readers must be able to identify the key version required by existing ciphertext. New writes use the active version. Re-encryption migrates old data deliberately. Once migration and retention requirements are satisfied, the deployment may raise its minimum accepted decryption version or revoke the retired key according to policy.

FS must not infer this lifecycle from ciphertext alone. The authoritative key-service policy remains outside the protocol core.

## 2. Transport profile

The reference transport uses mutual TLS for federation channels.

Required controls:

- authenticate the peer before transmitting federation payloads;
- validate the peer credential against explicit trust anchors;
- bind authenticated certificate identity to the admitted FS node identity/fingerprint;
- use encrypted application traffic only after successful authentication;
- reject expired, revoked, malformed, or otherwise invalid credentials;
- clear authenticated state when the channel closes;
- fail closed when authentication is lost;
- enforce the deployment's supported TLS version and cipher policy;
- prevent endpoint confusion by binding the authenticated identity to the intended peer;
- qualify replay and downgrade protections at the federation-protocol boundary.

Certificate issuance, renewal and revocation are deployment responsibilities. They must not be silently invented by the FS core.

## 3. Adapter mapping

The reference deployment must implement the existing contracts rather than introduce parallel security abstractions:

- `SecureKeyStore` owns protected key-material access and lifecycle interaction.
- `AuthenticatedTransport` owns channel establishment, peer authentication, encryption, and authentication state.
- `NodeAdmission` remains authoritative for node identity, fingerprint, expiry and revocation.
- `KeyAdmission` remains authoritative for node/key/fingerprint binding and key lifecycle decisions.

The adapter implementations should expose stable, testable behavior while keeping provider-specific SDKs, sockets, credentials, and operational policy outside the protocol data model.

## 4. Qualification matrix

A real deployment is not qualified until every applicable row has reproducible evidence.

| Area | Positive evidence | Negative/fail-closed evidence |
| --- | --- | --- |
| AEAD | encrypt/decrypt round trip; restart | modified ciphertext/AAD/key rejected |
| Nonce lifecycle | fresh nonce per encryption under a key | unsafe nonce reuse is prevented or rejected by provider design |
| Key rotation | new writes use new version; old data remains readable during migration | revoked/retired version becomes unusable according to policy |
| Key recovery | restart restores authorized key references | revoked authority is not silently restored |
| Peer auth | valid peer authenticates and sends | invalid/expired/revoked peer cannot send |
| Identity binding | certificate maps to admitted node fingerprint | identity mismatch is rejected |
| Transport state | authenticated channel exchanges payloads | close/authentication loss prevents subsequent sends |
| Replay | valid sequence/message accepted once | duplicate or stale federation input rejected |
| Endpoint binding | intended peer identity is explicit | credential for another endpoint cannot satisfy admission |

## 5. Evidence package

For each deployment, store only references and non-secret metadata in `docs/PRODUCTION_QUALIFICATION_RECORD.md`:

- exact FS artifact/commit;
- OS and architecture;
- exact provider package/image versions;
- dependency lock/provenance;
- algorithm and protocol configuration;
- key-service policy identifiers;
- trust-anchor and certificate-policy identifiers;
- executed qualification commands;
- CI run IDs;
- operational recovery results;
- external security review or audit references.

Never store credentials, private keys, tokens, plaintext key material, or secret configuration values in the evidence record.

## Release gate

This reference profile **does not unblock V1 by itself**. It becomes release evidence only after concrete implementations are deployed or independently exercised, their exact versions/configuration are recorded, positive and negative qualification results are reproduced, and required external security review/audit evidence exists.

Until then, the production security decision remains `BLOCKED`.
