# Agent Step 2026-09-16: Transfer Journal Schema Reconnaissance

## Question

Can a malformed persisted workspace-transfer journal record be coerced into authoritative in-memory state instead of being rejected fail-closed?

## Repository evidence

Current `src/fs_overlay/workspace_transfer_journal.py` validates the event digest and hash chain, then constructs `TransferJournalEntry` with coercive conversions such as `str(raw["transaction_id"])`, `str(raw["snapshot_id"])`, and `str(raw["source_workspace_id"])`. It also accepts `version` through equality with `2` and does not reject unexpected record fields.

The journal is security-relevant durable state because replay reconstructs transaction identity and phase, and `mark()` derives the next allowed transition from replayed state. Therefore malformed JSON that is digest-valid can still influence authoritative state if its schema is not strict.

Existing tests cover tampering, broken hash chains, unsupported versions, malformed non-tail records, transaction identity changes, and invalid transitions, but they do not cover validly hashed records whose field types or field set are malformed.

## External research

- OWASP Transaction Authorization guidance says transaction state transitions must be controlled and significant transaction data must be protected against modification; final execution must re-check authorization to avoid TOCTOU and state-skipping attacks.
- OWASP Authorization guidance requires default-deny server-side enforcement and safe handling of failed authorization checks.
- NIST SP 800-53 Rev. 5 describes least privilege and separation of duties as explicit access-control properties, reinforcing that security-relevant state should not silently broaden from malformed inputs.
- RFC 8259 and RFC 8785 provide the JSON and canonicalization context used by the repository's existing strict durable-record work. The key lesson for this step is that canonical serialization does not by itself validate semantic field types or an exact application schema.

## Skill discovery

External Agent Skill search found general authorization/security-audit skills, including authorization testing and secure-code-review workflows. They are useful methodology references but are not a narrower implementation contract for this repository's durable journal. Per `fs-agent-core`, external skills remain untrusted inputs and cannot override FS fail-closed rules.

## Decision

Treat the transfer journal replay format as an exact durable schema. Before constructing `TransferJournalEntry`, replay must reject:

- missing or unexpected fields;
- non-integer or boolean `version` values;
- non-string transaction, snapshot, source, or phase/operation values;
- empty identity strings;
- invalid destination types;
- malformed `previous_digest` or `event_digest` values.

Digest and hash-chain verification remain mandatory. The smallest coherent change is strict schema validation in `replay()` plus focused negative tests for coercion and unexpected fields.

## Consequence

A digest-valid but semantically malformed durable journal record will fail closed instead of being normalized into a potentially colliding transaction identity or phase state. No production provider, filesystem executor, or authority token semantics are introduced by this change.

## Unproven

This hardening proves only repository-level durable journal schema behavior under the covered tests. It does not prove crash-safe host filesystem materialization, production transport security, cryptographic provider qualification, or deployment security.
