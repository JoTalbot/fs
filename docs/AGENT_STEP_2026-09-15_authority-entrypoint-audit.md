# Authority entrypoint audit

Date: 2026-09-15

## Result

The transfer security boundary was audited for alternate authority-bearing entry
points. The current implementation has one canonical new-execution admission
path: `executor_preflight()`.

`validate_materialization_executor_preflight()` is only a typed facade over that
function. It does not duplicate or weaken the security gates. The canonical path
requires authenticated identity admission, an authenticated transport session,
policy authorization, exact transfer-authority provenance, durable authority
revocation, and a `PREPARED` journal transaction before returning executor
inputs. The returned transport is a fail-closed gate and the result grants no
host filesystem capability by itself.

## Legacy compatibility boundary

`validate_materialization_preflight()` remains only for the non-mutating legacy
API and existing compatibility tests. It intentionally accepts no identity or
transport evidence, so it must never be treated as execution authorization.
Future mutation code must call the executor preflight facade instead.

The legacy explicit `grant_transfer_authority()` constructor also remains for
compatibility. Policy-bound and authenticated callers must use the corresponding
policy/identity-bound issuance functions, and any future mutation executor must
revalidate the resulting provenance through `executor_preflight()` immediately
before mutation.

## Recovery separation

Recovery is not an executor mode. A recovery candidate is already
`MATERIALIZING`, while normal executor admission requires `PREPARED`. Recovery
therefore uses `recovery_preflight()` with an independently qualified evidence
verifier before reconciliation. Recovery audit evidence does not grant transfer
authority and does not mutate the host filesystem.

## Regression coverage

Executor tests now also cover an unauthenticated transport. This protects the
entrypoint boundary against a future caller accidentally treating an existing
transport object as sufficient without an authenticated session.

## Remaining production gate

No host filesystem mutation is enabled by this audit. Production still requires
an audited AEAD implementation, secure key storage/lifecycle, authenticated and
encrypted transport, authoritative trust-root and identity verification, target-
specific recovery evidence, and external security review.