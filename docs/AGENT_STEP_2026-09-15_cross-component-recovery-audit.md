# Agent Step: Cross-component Recovery and Authority Boundary Audit

Date: 2026-09-15
Repository: `JoTalbot/fs`
Branch: `main`

## Scope

Audit the current workspace-transfer path after the green CI baseline, focusing on the boundary between normal executor admission, crash recovery evidence, rollback evidence, durable journal state, and host filesystem mutation.

## Research

- `docs/ROADMAP_V1.md`: the V1 lifecycle requires restart, network loss, duplicate/replay, key rotation/revocation, and recovery validation before production federation.
- `docs/PRODUCTION_REFERENCE_PROFILE.md`: recovery, revocation, identity binding, and transport qualification must be evidenced independently; the reference profile does not itself qualify a deployment.
- `docs/ADAPTER_CONFORMANCE.md`: adapter tests are semantic contract checks only; production adapters require implementation-specific recovery, access-control, and lifecycle evidence.
- `AGENTS.md`: every substantive step requires fresh repository research, explicit status ownership, truthful validation reporting, and small atomic commits.

## Audit result

No new fail-open defect was found in the reviewed cross-component path.

1. `executor_preflight()` requires a ready plan, authoritative trust-root lookup, verified principal admission, exact policy binding, exact authority provenance, live durable authority-revocation state, matching `PREPARED` journal state, and only then validates the injected authenticated transport session.
2. `validate_materialization_executor_preflight()` is a facade over that canonical path. It does not create an alternate authorization route.
3. `recovery_preflight()` accepts only a `MATERIALIZING` transaction and identity-matched recovery evidence, requires an independent evidence verifier, and only then calls reconciliation. Recovery does not issue transfer authority or mutate host storage.
4. Recovery reconciliation is conservative: complete matching evidence can produce `COMMIT_PROVEN`; complete absent-destination plus rollback-safe and staging-absent evidence can produce `ABORT_PROVEN`; unknown, conflicting, incomplete, or residual-staging evidence remains `MANUAL_REVIEW`.
5. `validate_rollback_evidence()` independently requires a `MATERIALIZING` journal entry, exact transaction/snapshot identity, preserved source, destination absence, staging absence, and independent rollback verification before proving rollback safety.
6. The durable transfer journal uses explicit phases and hash-chain validation, and reopen/replay tests cover valid continuation, identity changes, corruption, unsupported versions, incomplete EOF tails, and concurrent state transitions.
7. `RecoveryAuditLog.append()` accepts a `RecoveryPreflightResult`, not a bare reconciliation plan. Audit events bind to the exact verified evidence digest and are themselves hash-chained. Audit history is evidence, not authority.
8. The materializer remains non-destructive. Its `commit()` intentionally raises `NotImplementedError` until a separately qualified crash-safe executor exists.

## Important boundary

The reviewed implementation deliberately does not inspect or mutate the real host filesystem during recovery classification. This is a safety property of the current reference implementation, not proof of production filesystem correctness. A future executor must revalidate authority, transaction state, identity, revocation, and target observations immediately before mutation and must provide independently qualified crash/rollback evidence.

## Validation

GitHub Actions CI #662 is the current observed green baseline for commit `5a5fcaa33f2c59ff8e93d8b83d6672fbbb51db8b`, with 18/18 jobs successful, including the configured Ubuntu/Windows/macOS Python matrix and candidate crypto-provider jobs. The current audit found no concrete code regression requiring a corrective implementation commit.

## Decision

Do not add speculative code merely to mark roadmap boxes. Preserve the current fail-closed boundaries and move the next implementation effort only when a concrete missing contract or reproducible failure is identified. Production V1 remains blocked pending concrete audited security providers, deployment-specific recovery evidence, interoperability evidence, and external security review.

## Next safe step

Continue with production-provider boundary qualification, especially concrete `SecureKeyStore` and `AuthenticatedTransport` implementations in an external deployment environment. Keep provider credentials, private keys, and secret configuration out of the repository.
