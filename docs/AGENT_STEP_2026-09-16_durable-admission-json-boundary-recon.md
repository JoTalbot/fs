# Agent Step 2026-09-16: Durable Admission JSON Parsing Boundary Recon

## Question

Can duplicate JSON object member names in durable node/key admission records be silently collapsed before the existing strict schema, hash-chain, and event-digest validation?

## Repository research

- `src/fs_overlay/durable_admission.py` was re-read from `main` at blob `ed7200f1b081bdef362c24a6aa31058c9374797f` before modification.
- `NodeAdmissionRecord.from_line()` and `KeyAdmissionRecord.from_line()` already enforce exact field sets, strict scalar types, canonical SHA-256 values, lifecycle/status constraints, and event-digest verification.
- Both parsers still call default `json.loads(line)`. Python's default object decoder keeps one value for a repeated object key, so duplicate members are removed before those validators execute.
- `tests/test_durable_admission.py` was re-read at blob `5fa6591a89081e4afc2ae5a922baa100d594a264`. Existing tests cover coercible scalar types, unknown fields, tampering, and lifecycle behavior, but do not prove duplicate-key rejection at the parser boundary.

## External research

- RFC 8259 §4 says JSON object names SHOULD be unique and warns that duplicate names produce unpredictable receiver behavior; implementations commonly keep only one duplicate member. citeturn0search0turn0search1
- RFC 8785 requires JSON objects used by its canonicalization scheme to have no duplicate property names, reinforcing that duplicate members are incompatible with deterministic canonical representations. citeturn0search5
- OWASP Developer Guide recommends fatal parse errors on duplicate JSON keys because parsers can apply different precedence rules. citeturn0search25
- External `secure-software-engineering` skill `magnus919/agent-skills/secure-software-engineering/SKILL.md` was inspected as advisory guidance for untrusted serialized data and enforceable validation boundaries. citeturn1search5

## Decision

Reuse a local duplicate-key rejection hook and pass it as `object_pairs_hook` to both durable admission record parsers. Convert duplicate-key failures into the existing malformed-record errors. Add node and key regressions proving both top-level and nested duplicate members are rejected before schema or digest validation.

Do not change authority semantics, lifecycle states, hash construction, or journal ordering. This is a parser-boundary hardening only.

## Why this fits FS

Durable admission records are authoritative input to node/key admission state after replay. The existing strict schema and hash-chain checks cannot inspect a member that a permissive parser already discarded. Rejecting ambiguous serialization before semantic validation preserves the fail-closed admission boundary without inventing new authority.

## What remains unproven

This step does not establish cryptographic authenticity of the durable admission journal itself; event digests provide integrity detection within the existing journal model, while authoritative trust, revocation, key custody, and production storage security remain separate qualification boundaries.
