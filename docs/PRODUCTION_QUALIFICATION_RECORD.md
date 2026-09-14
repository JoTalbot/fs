# Production Security Qualification Record

This template is evidence storage, not certification. Complete it only for the exact deployment artifact, provider versions, configuration, platform and operational controls being released.

## Deployment identity

- Deployment name: `<name>`
- Artifact/version: `<version or commit>`
- Target platform/architecture: `<platform/arch>`
- Qualification date: `<UTC date>`
- Qualification owner: `<owner>`
- Threat model/reference: `<document or identifier>`

## 1. AEAD / confidentiality provider

- Provider implementation: `<implementation>`
- Package and exact version: `<package==version>`
- Build/provenance: `<source, wheel, image digest, lockfile>`
- Algorithm/configuration: `<algorithm and fixed parameters>`
- Key size: `<bits>`
- Nonce/IV construction and uniqueness control: `<mechanism>`
- AAD format/version: `<format>`
- Maximum input/object size: `<limit>`
- Independent vectors/interoperability evidence: `<reference>`
- Security review/audit evidence: `<reference>`

### AEAD qualification evidence

- [ ] Round-trip encryption/decryption
- [ ] Modified ciphertext rejected
- [ ] Modified AAD rejected
- [ ] Structurally truncated/malformed envelope rejected
- [ ] Invalid key size rejected
- [ ] Nonce lifecycle is documented and qualified
- [ ] Restart behavior qualified
- [ ] Key rotation/retirement/revocation interaction qualified
- [ ] Exact dependency/provenance captured
- [ ] External security review/audit evidence attached where required

## 2. Secure key storage

- Provider implementation: `<implementation>`
- Exact version: `<version>`
- Storage model: `<HSM/KMS/vault/etc.>`
- Access-control model: `<least-privilege policy>`
- Key identifiers/fingerprints: `<non-secret identifiers only>`
- Rotation policy: `<policy/reference>`
- Revocation policy: `<policy/reference>`
- Backup/recovery policy: `<policy/reference>`
- Audit evidence: `<reference>`
- External security review/audit evidence: `<reference>`

### Key-storage qualification evidence

- [ ] Secret material is absent from source control
- [ ] Secret material is absent from ordinary configuration and logs
- [ ] Unknown key IDs fail closed
- [ ] Revoked keys fail closed
- [ ] Rotation across restart is qualified
- [ ] Recovery cannot silently restore revoked authority
- [ ] Administrative operations are auditable without exposing secret material
- [ ] Access is least-privilege

## 3. Authenticated/encrypted transport

- Provider implementation: `<implementation>`
- Exact version: `<version>`
- Protocol/configuration: `<protocol and parameters>`
- Peer identity binding: `<node identity/fingerprint mapping>`
- Trust-anchor policy: `<policy/reference>`
- Certificate/credential policy: `<policy/reference>`
- Revocation/expiry policy: `<policy/reference>`
- Endpoint/service identity policy: `<policy/reference>`
- External security review/audit evidence: `<reference>`

### Transport qualification evidence

- [ ] Peer authentication precedes payload transmission
- [ ] Authenticated peer identity is bound to admitted node identity
- [ ] Payload confidentiality is verified
- [ ] Authentication failure blocks subsequent sends
- [ ] Closing the channel clears authenticated state
- [ ] Replay protection is qualified
- [ ] Downgrade protection is qualified
- [ ] Endpoint-confusion protection is qualified
- [ ] Revocation/expiry behavior is qualified

## 4. Operational recovery

- Restart scenario: `<result/reference>`
- Key rotation scenario: `<result/reference>`
- Key revocation scenario: `<result/reference>`
- Transport authentication loss: `<result/reference>`
- Malformed input/failure recovery: `<result/reference>`
- Backup restoration: `<result/reference>`
- Incident/audit evidence: `<reference>`

## 5. Evidence provenance

Record the exact commands and immutable references used to produce qualification evidence. Do not paste secret values into this document.

- Test command(s): `<command>`
- Dependency lock/provenance: `<reference>`
- CI run(s): `<run URL/ID>`
- Platform/architecture: `<environment>`
- Configuration reference: `<non-secret configuration identifier>`
- External review/audit: `<reference>`

## Release decision

- [ ] All required providers are concrete and deployment-qualified.
- [ ] All required evidence is attached and reproducible.
- [ ] No unresolved security-review blocker remains.
- [ ] `docs/V1_RELEASE_GATE.md` reflects the evidence state.

**Decision:** `BLOCKED` until every required security provider and evidence item is complete.
