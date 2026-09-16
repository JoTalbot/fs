# Snapshot JSON Parsing Boundary Recon

## Question
Can duplicate JSON object members in persisted snapshots be collapsed by parsing before strict snapshot schema, identity, and Merkle-root validation?

## Sources
- Repository: `src/fs_overlay/storage_resilience.py`, `tests/test_snapshot_provenance.py`, current `main` before implementation.
- RFC 8259 §4: JSON object names SHOULD be unique; duplicate-name behavior is unpredictable across implementations. 
- RFC 8785: canonical JSON objects MUST NOT contain duplicate property names.
- OWASP Developer Guide: duplicate JSON keys may be processed differently by parsers; duplicate keys should produce fatal parse errors.
- OWASP Input Validation: validate structured input syntactically and semantically as early as possible.
- External skill: `secure-software-engineering` from `magnus919/agent-skills`, inspected as advisory guidance for untrusted serialized data and explicit evidence boundaries.

## Repository finding
`Snapshot.from_bytes()` already enforced an exact top-level field set, strict scalar types, canonical SHA-256 identifiers, snapshot identity, and Merkle-root verification. However, it used default `json.loads(data)`. Python's decoder materializes duplicate object members into a single mapping entry before the existing schema checks. The same parser behavior applies recursively to nested metadata dictionaries.

Therefore a persisted record with duplicate `generation`, `snapshot_id`, or nested metadata members can be syntactically accepted while the validator sees only the last value. Identity verification may then validate the collapsed representation rather than the original ambiguous wire representation.

## Decision
Reject duplicate JSON object member names during `Snapshot.from_bytes()` parsing with an `object_pairs_hook` that raises on the second occurrence. Treat the parser failure as the existing `snapshot JSON is invalid` boundary error.

Preserve:
- existing exact-field and type validation;
- canonical snapshot/object identifiers;
- identity verification;
- Merkle-root verification;
- immutable snapshot storage and path isolation;
- no new authority or recovery semantics.

## Regression evidence
Add tests for duplicate top-level and nested metadata members. The tests exercise the persisted snapshot read path rather than only the helper in isolation.

## What remains unproven
- This hardening does not certify snapshot storage against filesystem corruption beyond the existing identity/Merkle checks.
- GitHub Actions remains the authoritative runtime validation environment; no local test runner is available.
- This change does not establish production security qualification or release readiness.
