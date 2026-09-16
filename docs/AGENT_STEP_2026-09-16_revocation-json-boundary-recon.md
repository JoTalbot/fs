# Agent Step 2026-09-16: durable revocation JSON parsing boundary

Question: Can duplicate JSON object members in durable authority-revocation records be collapsed before strict schema and hash-chain validation?

Base commit: `09dacacdb81ed33b9d140949b16afd1a9ea2bfd9`

## Repository research

`src/fs_overlay/authority_revocation.py` already enforces an exact field set and exact scalar types in `RevocationRecord.from_line()`, then verifies the event digest. `AuthorityRevocationRegistry._replay()` is the authoritative restart/read path and validates sequence continuity, previous-digest linkage, and duplicate authority IDs. The remaining parser uses default `json.loads(line)`, so repeated object members are collapsed before these checks.

The registry is security-relevant durable authority state. Its replay path is used by `is_revoked()`, `records()`, and mutation refresh under the coordination lock. Therefore parser ambiguity is a concrete fail-closed boundary gap, not merely formatting strictness.

## External research

- RFC 8259 §4: JSON object names SHOULD be unique; non-unique names have unpredictable receiver behavior, with implementations variously keeping the last member, rejecting the object, or exposing all members. https://www.rfc-editor.org/rfc/rfc8259.html
- OWASP Developer Guide JSON guidance: do not use duplicate keys and generate fatal parse errors for duplicate keys because parsers may apply different precedence. https://owasp.org/www-project-developer-guide/
- OWASP Input Validation: structured input should be validated explicitly, with strict type/range handling rather than permissive coercion. https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- External skill discovery: `secure-software-engineering` was inspected as advisory guidance for untrusted serialized data and explicit residual-risk/evidence recording. It does not override the repository contract.

## Decision

Reuse the established `_reject_duplicate_object_keys` parser-boundary pattern in `RevocationRecord.from_line()`. Reject duplicate members before schema and digest validation. Preserve all existing authority, replay, sequencing, locking, and hash-chain semantics. Add top-level and nested duplicate-key regression tests.

## Consequence

A durable revocation record is either represented by one unambiguous JSON member per field or replay fails closed. No new authority semantics are introduced.

## Validation target

GitHub Actions full configured matrix. No local test runner is available.
