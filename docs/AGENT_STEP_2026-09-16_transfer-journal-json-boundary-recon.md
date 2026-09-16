# Agent Step 2026-09-16: Transfer Journal JSON Boundary Recon

## Question
Can duplicate JSON object member names in the durable workspace transfer journal be collapsed by parsing before schema and hash-chain validation, allowing two textual records to have different interpretations across parsers?

## Repository research
- `src/fs_overlay/workspace_transfer_journal.py` was reread at blob `218c10c428251906361fb59255a18039bd747f1b` before modification.
- `WorkspaceTransferJournal.replay()` uses default `json.loads()` and then validates the materialized dictionary.
- `_last_digest()` also uses default `json.loads()` and extracts `event_digest` from the materialized dictionary while constructing the next append record.
- The journal is append-only, hash-chained durable state. Replay reconstructs transaction phases and `recovery_candidates()` exposes transactions left in `MATERIALIZING` state.
- Existing schema validation rejects unexpected fields and wrong scalar types, but it cannot observe a duplicate member that the parser has already collapsed.
- `tests/test_workspace_transfer_journal.py` was reread at blob `4d98971da1b9fba9d91acf3fa60697e3997e9687` before modification. Existing tests cover digest tampering, broken chains, type/schema corruption, transitions, and malformed records, but not duplicate JSON members.

## External research
- RFC 8259 §4 says JSON object member names should be unique and explicitly notes that duplicate-name behavior is unpredictable across implementations. citeturn0search0
- OWASP Developer Guide JSON guidance recommends not using duplicate keys and generating fatal parse errors for duplicate keys because parsers may apply different precedence. citeturn0search25
- RFC 8785 requires JSON objects used by its canonical JSON processing to have no duplicate property names. citeturn0search5

## Skill discovery
- External `secure-software-engineering` skill from `magnus919/agent-skills` was inspected as advisory guidance for untrusted serialized input and evidence-backed security controls. citeturn1search0
- It does not override the repository-local `fs-agent-core` contract.

## Decision
Reject duplicate JSON object member names during parsing of every durable workspace transfer journal record. Use the same strict parser in `_last_digest()` so both replay and append-time previous-digest discovery observe the same wire representation. Preserve the existing record schema, framing, SHA-256 event digest, hash-chain semantics, transition rules, and authority boundaries.

## Acceptance criteria
1. Any duplicate member at the top level of a transfer journal record raises `TransferJournalCorruption` before schema/digest processing.
2. Duplicate members nested inside any future structured value are also rejected by the same parser policy.
3. `_last_digest()` cannot silently consume a different interpretation of persisted JSON.
4. Existing valid records and hash-chain behavior remain unchanged.
5. Regression coverage demonstrates rejection of duplicate `event_digest` and another duplicate record field while preserving valid replay.

## Unproven / residual
- This hardening covers the workspace transfer journal parser only. Other JSON consumers require their own boundary review.
- It does not constitute production security certification or prove the future host filesystem executor is crash-safe.
