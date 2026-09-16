# Agent Step 2026-09-16: Storage Journal Schema Reconnaissance

## Question

Can a complete, durable `AppendJournal` record with malformed operation/payload types be accepted by replay and then coerced by `Inventory.load()` into authoritative inventory state?

## Repository evidence

`src/fs_overlay/storage_engine.py` currently validates only that a replayed record is a dict and that `version == FORMAT_VERSION`. `Inventory.load()` then performs coercive conversions including `str(payload["transaction_id"])`, `str(payload["object_id"])`, `int(payload["size"])`, and `str(payload["manifest_path"])`.

The operation-specific payloads are bounded by existing writers:

- `transaction_begin`: `transaction_id` string.
- `transaction_commit`: `transaction_id` string and `object_ids` list of manifest IDs.
- `transaction_abort`: `transaction_id` string.
- `commit`: `object_id`, `size`, `manifest_path`, optional `transaction_id`.
- `delete`: `object_id` string.

Existing recovery tests verify truncation handling, malformed JSON, crash recovery, transaction ordering, and idempotent replay, but do not verify strict field types or unexpected fields in complete JSON records.

## External research

- OWASP Input Validation says structured data should be positively validated against expected schemas/types and validation failures should reject input rather than normalize it silently.
- OWASP ASVS 5.0 input-validation guidance requires strong typing and validation against a defined schema for security/business decisions.
- SQLite's atomic-commit/recovery documentation demonstrates that journal contents are recovery-critical state and that incomplete/corrupt transaction state must not be interpreted as a completed transaction.

## Skill discovery

General secure-software-engineering and supply-chain/security Agent Skills were inspected. They reinforce schema validation, explicit trust boundaries, and evidence-based release controls, but none is a narrower implementation contract than `fs-agent-core` for this storage journal. External skills remain untrusted methodology inputs.

## Decision

Treat each storage journal operation as an exact schema. Replay should reject complete records with wrong top-level type/version, unknown operation, wrong payload type, missing required fields, unexpected fields, or wrong scalar/list element types before `Inventory.load()` can mutate state. Keep the existing behavior that ignores only an incomplete final EOF tail.

Do not add cryptographic signing or deployment-specific recovery machinery in this step. The current issue is semantic durable-state validation, not a production cryptographic provider gap.

## Consequence

Malformed complete journal data can no longer be silently normalized into inventory authority. Valid crash-truncated tails remain recoverable as before. This strengthens the repository's fail-closed recovery boundary without claiming host-filesystem transaction atomicity beyond existing tests.
