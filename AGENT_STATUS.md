# FS Agent Status

> Shared coordination state for parallel AI agents. Update this file at every substantive step boundary.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Current architecture: portable local storage substrate with federation/control-plane reference primitives and explicit production-adapter boundaries.
- Updated: 2026-09-10

## Completed federation/control-plane foundation

- Explicit `NodeIdentity` and fingerprint-bound `TrustStore` with expiry/revocation.
- Signed capability advertisements with fail-closed trust and freshness admission.
- Monotonic `FederationDirectory` observations and deterministic reconciliation planning.
- Canonical `FederationEnvelope` with SHA-256 digest, signature boundary, replay protection, and deterministic byte serialization.
- Journal-backed `DurableFederationState` for accepted message IDs and sender sequence high-water marks across restart.
- Durable replay reconstruction now fails closed on malformed accepted-state identity/sequence regressions; admission is serialized for threads sharing one state instance.
- `DurableFederationState` accepts an injected admission coordinator and holds it across validation, journal emission, and state mutation.
- Coordinated admissions refresh both the durable state indexes and `EventLog` sequence/hash state while holding the coordinator, preventing long-lived multi-process writers from making decisions from stale high-water marks or emitting duplicate event sequences.
- `EventLog.reload()` provides an explicit refresh boundary for processes that coordinate externally before emitting new journal records.
- `FileAdmissionCoordinator` provides an explicit local cross-process coordination adapter using OS file locks, with deterministic resource paths, bounded acquisition timeout, retained lock files, and no stale-lock stealing.
- Crash semantics are covered: the adapter relies on the operating system to release a held lock when the owning process exits; it never deletes or steals a supposedly stale lock.
- `DurableAdmissionCoordinator` is runtime-checkable for structural adapter conformance.
- `FederationAuditTrail` linking reconciliation decisions to replica execution results through causal event chains.
- Verified `ReplicaExecutor` with source and post-copy target integrity checks.
- Deterministic `SelfHealingPlanner` from explicit trusted/healthy observations.
- Failure-domain-aware `ReplicaPolicy` with deterministic candidate ordering.
- Transport, signing, and key-provider dependency-injection contracts.
- Deterministic capability negotiation with protocol-version fail-closed behavior.
- Explicit key lifecycle model for active, retired, and revoked keys, including fail-closed duplicate-ID and silent-fingerprint-change checks.
- Versioned federation conformance vectors and envelope round-trip tests.
- `MinimalInitiator` that requires explicit bootstrap configuration and injected key/signing/transport capabilities, and sends the complete signed envelope without peer discovery.
- Cross-platform capability discovery remains conservative and host-local.
- Minimal bootstrap creates only an explicitly selected FS root and atomic configuration.
- Explicit production security adapter contracts for protected key storage, authenticated/encrypted transport, authoritative node admission/revocation, and node/key lifecycle admission.
- Versioned interoperability boundary documentation and fail-closed strict conformance validation for published vectors.
- Published protocol-v1 conformance vectors are consumable as standalone JSON data under `conformance/v1/`, including a UTF-8/non-ASCII payload vector.
- Added dependency-free independent conformance consumer under `tools/`, deliberately avoiding `fs_overlay` imports.
- Independent consumer validates the declared protocol version and canonicalization contract instead of silently hard-coding assumptions from vector metadata.
- Published protocol-v1 admission-negative vector set now defines ten required fail-closed cases: malformed envelope; unsupported protocol; negative sequence; empty ID; duplicate ID; sequence rollback; stale/future timestamps; missing signature; and key-admission failure covering unknown/revoked/fingerprint mismatch.
- Added dependency-free independent admission validator that checks the ten-case negative contract without importing `fs_overlay`.
- CI executes both independent conformance validators before the internal pytest suite on the full Ubuntu/Windows/macOS and Python 3.11/3.12/3.13 matrix.

## Safety boundaries

The reference implementation does not silently scan or modify the host, discover arbitrary peers, grant trust from discovery, select unauthorized carriers, or claim distributed consensus. Network transport, production cryptography, secure key storage, concurrency coordination, and deployment-specific policy remain explicit adapters/operational boundaries.

The durable federation state lock serializes concurrent threads within one process only. It does not claim multi-process atomicity. Deployments with multiple writers must supply an explicit `DurableAdmissionCoordinator` or equivalent file-locking/transactional backend.

`FileAdmissionCoordinator` is an adapter, not distributed consensus and not a transaction spanning the coordination lock and `EventLog`. Lock files are retained; there is no stale-lock deletion or lock stealing. Timeout means bounded waiting only. A crashed owner relies on OS lock release. Windows and POSIX locking behavior are isolated in the adapter and validated by the CI matrix.

Coordinated writers refresh durable admission indexes and journal sequence/hash state after acquiring the lock. This closes the stale-reader gap without claiming cross-store ACID atomicity.

## Validation

- GitHub Actions CI run #217 (`5fe36cea`) completed successfully across all 9 matrix jobs for Python 3.11, 3.12 and 3.13 on Ubuntu, Windows and macOS.
- Run #233 exposed a real synchronization flaw in the crash test: `multiprocessing.Queue` could lose its notification when the child called `os._exit()`. The test was corrected to use a process-shared `Event`.
- Run #233 also showed the suite reached 186 passed / 3 skipped with only that test failing on the then-current commit; the failure was test synchronization, not the coordinator implementation.
- GitHub Actions CI run #242 completed successfully across all 9 OS/Python matrix jobs for Python 3.11, 3.12 and 3.13 on Ubuntu, Windows and macOS.
- GitHub Actions CI run #244 completed successfully across all 9 OS/Python matrix jobs for Python 3.11, 3.12 and 3.13 on Ubuntu, Windows and macOS.
- GitHub Actions CI run #248 completed successfully after strict conformance regression coverage.
- GitHub Actions CI run #249 completed successfully after the interoperability boundary documentation update.
- CI run #252 completed successfully across all 9 OS/Python matrix jobs, including the independent conformance consumer.
- CI run #255 completed successfully across all 9 OS/Python matrix jobs, including the UTF-8 vector.
- CI run #256 completed successfully across all 9 OS/Python matrix jobs, including the hardened consumer and UTF-8 vector.
- CI run #262 exposed a contract-integration defect: the newly added admission vector was discovered by the canonical consumer, which expected `vector_id` and canonical envelope fields. The vector was made self-describing and the canonical consumer now delegates `vector_type=admission` to the dedicated semantic validator.
- The admission vector/validator were then aligned to the intended ten-case contract, and interoperability documentation was corrected accordingly.
- A fresh CI run is triggered by the fix and must be green across all 9 jobs before this batch is considered validated.
- Local pytest execution is not claimed because the current environment cannot resolve GitHub for repository cloning.
- No production cryptographic certification, distributed transaction guarantee, remote-copy guarantee, or native-platform guarantee is claimed from these reference primitives.

## Release-readiness boundary

The codebase now has the reference architecture needed to implement platform-specific production adapters without changing the core protocol model. A production deployment still requires audited cryptographic algorithms/providers, authenticated and encrypted transport, secure key lifecycle storage, persistent/compacted replay state, multi-process/concurrency rules, failure-domain policy backed by authoritative observations, interoperability with an independent implementation, and operational recovery testing.

## Next phase

- Validate the corrected ten admission-negative cases across the full CI matrix.
- Expand conformance only where expected wire/semantic results can be specified independently of the reference implementation.
- Build adapter-specific conformance tests for authoritative production backends without faking security guarantees in the reference layer.
- The reference file coordinator remains the local multi-process implementation; it must not be promoted to a distributed/ACID guarantee.
- Platform-specific locking differences must be fixed in the adapter rather than weakening the regression gate.
