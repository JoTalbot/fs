# Agent Step 2026-09-16: Trust-root JSON Parsing Boundary Recon

## Question
Can duplicate JSON object members in durable trust-root records be silently collapsed before strict schema and hash-chain validation?

## Repository research
- `src/fs_overlay/trust_roots.py` uses `TrustRootRecord.from_line()` to parse each durable JSONL record.
- The parser already enforces an exact field set, strict scalar types, canonical lowercase SHA-256 values, sequence continuity, previous-digest linkage, and event-digest verification.
- It still calls `json.loads(line)` with the default object parser. Duplicate members are therefore collapsed before those checks.
- `DurableTrustRootStore._replay()` is the authoritative restart/read path for trust-root state, and `trust()`, `revoke()`, `issuer_fingerprint()`, and `records()` all replay durable state under the file coordination lock.
- Existing `tests/test_trust_roots.py` covers tampering and scalar/schema rejection but does not exercise duplicate top-level or nested JSON members.

## Internet research
- RFC 8259 section 4 says JSON object names should be unique and warns that duplicate names produce unpredictable receiver behavior, including implementations that retain only the last member. https://www.rfc-editor.org/rfc/rfc8259.html
- OWASP Developer Guide recommends not using duplicate JSON keys and generating fatal parse errors because parsers can differ in first-key/last-key handling. https://owasp.org/www-project-developer-guide/assets/exports/OWASP_Developer_Guide.pdf
- OWASP Input Validation recommends early syntactic validation of untrusted structured input and rejection of malformed content. https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html

## Skill discovery
- Canonical `.agents/skills/fs-agent-core/SKILL.md` was reread from `main`.
- Its durable JSON journal rule explicitly requires duplicate object member rejection at every parse path before schema or digest validation.
- No additional external skill was needed beyond the already applicable secure input-validation guidance.

## Decision
Reuse the repository's existing `_reject_duplicate_object_keys` pattern in the trust-root parser and reject duplicate object members before the existing schema/hash-chain checks. Add isolated regressions for duplicate top-level and nested JSON members and verify restart admission fails closed.

## Consequence
The change affects only parsing ambiguity. It does not change trust-root authority semantics, lifecycle transitions, fingerprint validation, hash-chain semantics, or cryptographic verification responsibilities.

## Unproven
This repository-level change does not constitute production trust-anchor qualification, secure key custody, or independent security certification.
