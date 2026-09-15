# Agent step: authority revocation boundary

Date: 2026-09-15

## Change

Added `AuthorityRevocationRegistry`, an append-only durable registry for explicit transfer-authority revocation. Each record is bound to an `authority_id` and carries a sequence number plus SHA-256 hash-chain linkage. Records are flushed and fsynced before becoming visible to the in-memory registry.

Replay is fail-closed: malformed records, digest mismatches, sequence discontinuity, hash-chain breaks, and duplicate authority revocations reject registry startup. Reopening the registry reconstructs the same revocation state.

## Materializer boundary

`validate_materialization_preflight()` can now consume a revocation registry. When supplied, it requires authority provenance and rejects revoked authorities before returning preflight evidence. The registry is deliberately separate from recovery audit, so audit decisions cannot accidentally become revocation authority.

## Safety boundary

- Revocation is explicit and durable.
- Revocation state is not inferred from filesystem capability or audit state.
- Authority IDs are correlation/integrity identifiers, not authentication credentials.
- The registry does not authenticate principals, manage keys, or mutate the host filesystem.
- Existing legacy authority issuance remains compatible when no revocation registry is supplied; a revocation-aware path requires provenance.
- Host filesystem execution remains disabled.

## Tests

Added durable restart, duplicate, tamper, chain-break, and sequence-discontinuity tests. Added materializer regressions for revoked authority and missing provenance during revocation-aware preflight.

## Remaining security gate

Before enabling any executor, bind revocation to authenticated principal/issuer trust, define key and transport lifecycle, and qualify concurrent issuance/revocation semantics. Revocation must remain fail-closed across restart and crash recovery.
