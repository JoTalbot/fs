# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Current architecture: portable local storage substrate with federation/control-plane reference primitives and explicit production-adapter boundaries.
- Updated: 2026-09-12

## Current V1 position

The reference V1 qualification program is substantially complete. The latest release-gate evidence has all semantic/protocol checklist items green. V1 is **not** declared production-ready because deployment-specific security providers still require concrete qualification evidence, including a real audited AEAD implementation, secure key storage, and authenticated/encrypted transport.

Latest validation commits/runs:

- `b39b19ea562e9eb5ffd5332424c8e6ce2408df09`: fixed the signed two-node recovery fixture.
- CI run #311: 9/9 supported Ubuntu/Windows/macOS Python 3.11/3.12/3.13 jobs green.
- `6b73c998749996f6230daa3d9f55e3d523f88c95`: added semantic qualification for the `AuthenticatedEncryption` provider boundary.
- `ed1d6d4844db5aaa49e39208144f13c20ca451ac`: defined the production cryptography qualification gate; CI run #313 green.
- `58794593c76017117a29ce8d5b8729cfd71d0d2e`: updated V1 release-gate evidence; CI run #314 green.
- `d1624ec8dd97af19abf0c48abcf21fdfc0e27e15`: added `docs/PRODUCTION_SECURITY_QUALIFICATION.md` defining the concrete production-provider evidence record.

## Completed federation/control-plane foundation

- Explicit `NodeIdentity` and fingerprint-bound `TrustStore` with expiry/revocation.
- Signed capability advertisements with fail-closed trust and freshness admission.
- Monotonic `FederationDirectory` observations and deterministic reconciliation planning.
- Canonical `FederationEnvelope` with SHA-256 digest, signature boundary, replay protection, and deterministic byte serialization.
- Journal-backed `DurableFederationState` for accepted message IDs and sender sequence high-water marks across restart.
- Durable replay reconstruction fails closed on malformed accepted-state identity/sequence regressions; admission is serialized for threads sharing one state instance.
- `DurableFederationState` accepts an injected admission coordinator and holds it across validation, journal emission, and state mutation.
- Coordinated admissions refresh durable state indexes and `EventLog` sequence/hash state while holding the coordinator.
- `EventLog.reload()` provides an explicit refresh boundary for processes that coordinate externally before emitting new journal records.
- `FileAdmissionCoordinator` provides local cross-process coordination using OS file locks, bounded acquisition timeout, retained lock files, and no stale-lock stealing.
- Crash semantics rely on OS lock release; the adapter never deletes or steals a supposedly stale lock.
- Production adapter protocols are runtime-checkable for structural conformance.
- `FederationAuditTrail` links reconciliation decisions to replica execution results through causal event chains.
- Verified `ReplicaExecutor` performs source and post-copy target integrity checks.
- Deterministic `SelfHealingPlanner` uses explicit trusted/healthy observations.
- Failure-domain-aware `ReplicaPolicy` has deterministic candidate ordering.
- Transport, signing, and key-provider dependency-injection contracts.
- Deterministic capability negotiation with protocol-version fail-closed behavior.
- Explicit key lifecycle model for active, retired, and revoked keys, including fail-closed duplicate-ID and silent-fingerprint-change checks.
- Versioned federation conformance vectors and envelope round-trip tests.
- `MinimalInitiator` requires explicit bootstrap configuration and injected key/signing/transport capabilities and sends the complete signed envelope without peer discovery.
- Cross-platform capability discovery remains conservative and host-local.
- Minimal bootstrap creates only an explicitly selected FS root and atomic configuration.
- Explicit production security adapter contracts for protected key storage, authenticated/encrypted transport, authoritative node admission/revocation, and node/key lifecycle admission.
- Versioned interoperability boundary documentation and strict conformance validation for published vectors.
- Published protocol-v1 conformance vectors are consumable as standalone JSON data under `conformance/v1/`.
- Dependency-free independent conformance and admission validators deliberately avoid `fs_overlay` imports.
- CI executes both independent validators before the internal pytest suite on the full supported matrix.
- Adapter-specific qualification tests cover positive and negative capability cases.
- Ambiguous durable-admission recovery is executable across process crash/restart.
- Canonical serialization/replay properties are qualified.
- Recovery graph rejects cycles and produces deterministic plans.
- Carrier changes enter quarantine rather than silent overwrite.
- Compatibility/version policy is documented and tested fail-closed.
- Minimal federation E2E lifecycle and deterministic two-node recovery are reproducible from tests.
- `AuthenticatedEncryption` now has semantic provider-boundary qualification tests; these intentionally do not certify cryptographic strength.
- `docs/PRODUCTION_SECURITY_QUALIFICATION.md` records the required evidence for real production AEAD, secure key storage, and authenticated/encrypted transport providers.

## Safety boundaries

The reference implementation does not silently scan or modify the host, discover arbitrary peers, grant trust from discovery, select unauthorized carriers, or claim distributed consensus. Network transport, production cryptography, secure key storage, concurrency coordination, and deployment-specific policy remain explicit adapters/operational boundaries.

The durable federation state lock serializes concurrent threads within one process only. It does not claim multi-process atomicity. Deployments with multiple writers must supply an explicit `DurableAdmissionCoordinator` or equivalent file-locking/transactional backend.

`FileAdmissionCoordinator` is an adapter, not distributed consensus and not a transaction spanning the coordination lock and `EventLog`. Lock files are retained; there is no stale-lock deletion or lock stealing. Timeout means bounded waiting only. A crashed owner relies on OS lock release. Windows and POSIX locking behavior are isolated in the adapter and validated by the CI matrix.

If a durable append outcome is ambiguous, the current in-memory process must not guess. Recovery must reconstruct authoritative admission state from durable storage before retrying or treating the message as newly admitted.

## Validation

- CI run #304 passed the full 9-job matrix for coordinated durable-admission crash recovery.
- CI run #305 passed the full matrix for canonical serialization and replay invariant qualification.
- CI run #311 passed all 9 supported Ubuntu/Windows/macOS Python 3.11/3.12/3.13 jobs, including independent federation and admission conformance before pytest.
- CI run #313 passed all 9 supported jobs after the production cryptography qualification gate documentation.
- CI run #314 passed all 9 supported jobs after the V1 release-gate evidence update.
- All current supported jobs execute the independent conformance consumer, independent admission validator, and internal pytest suite successfully.
- FreeBSD native CI remains intentionally disabled and outside the current release gate.
- No production cryptographic certification, distributed transaction guarantee, remote-copy guarantee, or native-platform guarantee is claimed from the reference primitives.

## Release-readiness boundary

The semantic V1 release gate is green except for the deliberate production confidentiality-provider checkbox. A production deployment still requires:

1. a real audited AEAD provider selected and qualified for the exact deployment;
2. secure key lifecycle storage with access control, rotation, revocation, backup/recovery and audit evidence;
3. authenticated and encrypted transport with explicit certificate/trust/revocation policy where applicable;
4. target-specific provider qualification and operational recovery evidence.

The repository's HMAC integrity envelope and deterministic AEAD test double must never be presented as production confidentiality.

## Next phase

- Select concrete production security providers per deployment target without changing the protocol contracts.
- Run provider-specific positive/negative, restart, rotation/revocation and failure-mode qualification.
- Record exact provider versions/configuration and external security-review/audit evidence in the production qualification record.
- Keep the V1 gate blocked until those provider records exist.
- After production security qualification, advance to operational interoperability, deployment packaging, and broader federation-scale testing.
