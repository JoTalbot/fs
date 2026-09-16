# Storage Journal JSON Parsing Boundary Recon

## Question
Can duplicate JSON object members in complete persisted `AppendJournal` frames be silently collapsed before journal schema validation and `Inventory.load()` reconstruction?

## Sources
- Repository: `src/fs_overlay/storage_engine.py`, `tests/test_storage_transaction_recovery.py`, current `main`.
- RFC 8259 §4: duplicate JSON object names have unpredictable receiver behavior; interoperable objects should use unique names.
- RFC 8785: canonical JSON objects MUST NOT contain duplicate property names.
- OWASP Developer Guide: duplicate JSON keys may be processed differently by parsers and should produce fatal parse errors.
- Canonical `fs-agent-core`: durable JSON journals must reject duplicate members before schema or digest validation.

## Repository finding
`AppendJournal.replay()` parses each complete length-prefixed frame with default `json.loads(body)`. It then checks the exact outer record fields, version, operation type, and payload dictionary. Duplicate outer fields and duplicate nested payload fields are therefore collapsed before those checks. `Inventory.load()` consumes the resulting payload and reconstructs durable inventory state. This is a concrete parser-boundary gap in the durable recovery path.

## Decision
Reuse the existing `_reject_duplicate_object_keys` helper in `storage_engine.py` and pass it as `object_pairs_hook` to `json.loads()` in `AppendJournal.replay()`. Convert the hook's `ValueError` into the existing `JournalCorruption("journal contains malformed JSON")` boundary. Preserve framing semantics: only incomplete EOF tails remain ignorable; a complete duplicate-key frame fails closed.

## Regression evidence
Add complete-frame regressions for duplicate top-level journal fields and duplicate nested payload fields. Exercise `AppendJournal.replay()` directly and `LocalStorageEngine` restart/reconstruction for the latter so no malformed durable record can reach inventory state.

## What remains unproven
This hardening only addresses duplicate JSON member ambiguity. It does not establish production storage crash consistency beyond the existing journal contract, filesystem durability guarantees, or production security qualification.

GitHub Actions remains authoritative; no local test runner is available.
