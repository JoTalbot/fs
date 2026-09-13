# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Current architecture: portable local storage substrate with federation/control-plane reference primitives and explicit production-adapter boundaries.
- Updated: 2026-09-14

## Current V1 position

The reference V1 qualification program is substantially complete. The semantic/protocol foundation remains qualified, but V1 is **not** declared production-ready. Deployment-specific security providers still require concrete qualification evidence, including a real audited AEAD implementation, secure key storage, and authenticated/encrypted transport.

A new candidate AES-GCM adapter was deliberately added as an opt-in provider. Its semantic tests exposed a CI dependency regression: the normal `.[test]` extra does not install `cryptography`, so the supported matrix currently fails when those candidate tests instantiate the provider. This is recorded as a real red-CI state and is not being hidden with conditional skips.

## Latest validation state

Previously validated:

- `b39b19ea562e9eb5ffd5332424c8e6ce2408df09`: fixed the signed two-node recovery fixture.
- CI run #311: 9/9 supported Ubuntu/Windows/macOS Python 3.11/3.12/3.13 jobs green.
- `6b73c998749996f6230daa3d9f55e3d523f88c95`: added semantic qualification for the `AuthenticatedEncryption` provider boundary.
- `ed1d6d4844db5aaa49e39208144f13c20ca451ac`: defined the production cryptography qualification gate; CI run #313 green.
- `58794593c76017117a29ce8d5b8729cfd71d0d2e`: updated V1 release-gate evidence; CI run #314 green.
- `d1624ec8dd97af19abf0c48abcf21fdfc0e27e15`: added `docs/PRODUCTION_SECURITY_QUALIFICATION.md` defining the concrete production-provider evidence record.
- `363870cde754a932727d9d188f77e59cc37c7e4b`: added the opt-in `CryptographyAESGCM` candidate adapter.
- `f9ba3ef797100726fa8db65b4fba7accb471b687`: added semantic tests for the candidate AES-GCM adapter.
- `acdef616833ecffb1ad3db300c44cb1888a146b6`: recorded that the AES-GCM adapter is candidate-only and not audited production evidence.
- `68ba1fc080d25cbe303f8e3f735a5dd66bd60e93`: defined the production secure-key-storage provider plan.
- `a59bbf0e1b87180e09509b1c2d51fa160b6bf24f`: added the production provider qualification runbook.

Current regression evidence:

- CI run `34784220152`: all 9 supported matrix jobs fail at the pytest step after both independent conformance validators pass.
- Representative Ubuntu 3.11 job: `259 passed, 3 skipped, 4 errors`.
- All four errors are candidate AES-GCM tests failing because `cryptography` is absent from the installed `.[test]` environment.
- The failure is specifically `ModuleNotFoundError: No module named 'cryptography'`, followed by the adapter's intentional runtime error explaining that the crypto extra is required.
- The same failure pattern is present across the supported Ubuntu/Windows/macOS Python 3.11–3.13 matrix.

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
- CI run `34784220152` is currently red across all 9 supported jobs because the candidate AES-GCM tests require a dependency not present in `.[test]`.
- Independent federation and admission conformance still pass in the failing run, isolating the regression to the candidate provider test layer.
- Candidate AES-GCM tests therefore must not be represented as green CI evidence yet.
- FreeBSD native CI remains intentionally disabled and outside the current release gate.
- No production cryptographic certification, distributed transaction guarantee, remote-copy guarantee, or native-platform guarantee is claimed from the reference primitives.

## Release-readiness boundary

The semantic V1 release gate remains blocked on production security evidence. In addition, the candidate-provider CI regression must be resolved without weakening the test signal.

A production deployment still requires:

1. a real audited AEAD provider selected and qualified for the exact deployment;
2. secure key lifecycle storage with access control, rotation, revocation, backup/recovery and audit evidence;
3. authenticated and encrypted transport with explicit certificate/trust/revocation policy where applicable;
4. target-specific provider qualification and operational recovery evidence;
5. a green supported CI matrix after the candidate-provider qualification path is correctly wired.

The repository's HMAC integrity envelope and deterministic AEAD test double must never be presented as production confidentiality. The `CryptographyAESGCM` adapter is a concrete candidate only and does not satisfy the audit requirement by itself.

## Next phase

- Establish a controlled dependency path for the candidate AEAD provider without changing the protocol contract.
- Keep candidate-provider tests explicit rather than skipping them when the provider is unavailable.
- Run provider-specific positive/negative, restart, rotation/revocation and failure-mode qualification on the exact deployment artifact.
- Select and qualify concrete secure key-storage and authenticated/encrypted transport providers per deployment target.
- Record exact provider versions/configuration and external security-review/audit evidence in the production qualification record.
- Re-run the full Ubuntu/Windows/macOS Python 3.11–3.13 matrix and require 9/9 green before advancing the gate.
- Keep the V1 gate blocked until those provider records and green CI evidence exist.
- After production security qualification, advance to operational interoperability, deployment packaging, and broader federation-scale testing.
