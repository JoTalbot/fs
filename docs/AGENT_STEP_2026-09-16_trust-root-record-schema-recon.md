# Trust-root persisted record schema reconnaissance

Date: 2026-09-16

## Scope

Review `TrustRootRecord.from_line()` and durable trust-root replay for fail-closed handling of malformed persisted records before those records become authoritative trust-root state.

## Repository findings

`src/fs_overlay/trust_roots.py` stores an append-only sequence of trust-root records. Replay already enforces nonblank lines, contiguous sequence numbers, previous-digest linkage, and event-digest integrity.

The persisted parser currently coerces several fields with `int(...)` and `str(...)`. That permits wrong JSON scalar types to be converted into authoritative values. For example, a boolean can be accepted as an integer sequence through Python's `int()` semantics, and numeric or boolean values can be converted to strings for issuer and digest fields. The parser also does not reject unexpected top-level fields before constructing the record.

Because the resulting record controls the durable trust-root registry, schema validation must precede digest/hash-chain evaluation and authoritative replay state construction.

## External research

OWASP input-validation guidance recommends validating untrusted structured data at the earliest boundary, using syntactic and semantic validation, strong types/ranges, schema validation, and rejection of unexpected content. NIST SP 800-57 identifies trust anchors as foundational key-management material whose authenticity and integrity are security-critical assumptions.

## Decision

Harden only `TrustRootRecord.from_line()` and its regression coverage. Require the exact persisted field set and exact JSON scalar types, reject boolean-as-integer sequence values, validate canonical SHA-256 fields and semantic ranges before digest/hash-chain use, and preserve existing event-digest/hash-chain and replay semantics. Do not alter trust-root authority semantics, cryptographic verification responsibilities, or storage coordination.

## Validation plan

GitHub Actions is the authoritative validation environment. Add deterministic negative regressions for wrong field types and unexpected persisted fields, then require the configured CI matrix to pass before closing the boundary.
