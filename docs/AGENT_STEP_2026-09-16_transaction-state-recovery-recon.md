# Agent step: durable transaction state-transition recovery reconnaissance

Date: 2026-09-16
Agent: `gpt-5.6-luna`
Base commit: `b1280e66cf531b7fdb952e262318f0a90394eb41`

## Question

Can malformed durable transaction state transitions in `Inventory.load()` be silently ignored or overwrite pending recovery state in a way that changes recovered inventory without a valid transaction lifecycle?

## Repository research

Current `Inventory.load()` validates each transaction payload, but its state handling is permissive:

- `transaction_begin` assigns `pending[transaction_id] = []`, so a second begin for the same ID discards any staged commit records already accumulated under that ID.
- `transaction_commit` executes `pending.pop(transaction_id, [])`, so a commit for an unknown ID silently does nothing.
- `transaction_abort` executes `pending.pop(transaction_id, None)`, so an abort for an unknown ID silently does nothing.
- A `commit` carrying a transaction ID uses `pending.setdefault(transaction_id, []).append(payload)`, allowing staged data to appear without a preceding begin; the later terminal marker may still be a no-op.
- `transaction_commit.object_ids` is schema-validated but is not compared with the staged commit records that recovery actually publishes.

The current `StorageTransaction.commit()` emits the intended lifecycle in order: begin, zero or more staged commit records, terminal commit, then in-memory publication. `rollback()` emits a terminal abort. Existing crash/restart tests exercise valid ordering and partial publication, but do not assert rejection of out-of-order or duplicate transaction lifecycle records.

## External research

- SQLite's atomic-commit documentation describes transaction state as an all-or-nothing unit and uses durable journal state to distinguish incomplete work from committed work. citeturn0search0turn0search3
- SQLite's isolation documentation describes serialized writes and transaction recovery semantics. citeturn0search2
- OWASP Transaction Authorization requires transaction state transitions to occur in sequential order and explicitly calls out prevention of skipped or out-of-order steps. citeturn0search1
- The external `secure-software-engineering` skill recommends explicit security acceptance criteria, enforceable server-side controls, and direct evidence for security-sensitive state transitions. citeturn1search0
- The searched distributed-data/durability skill material reinforces atomicity, retry/recovery ordering, and durable-write evidence as distinct concerns. It is advisory only.

## Decision

Treat durable transaction records as a small state machine for replay:

`ABSENT -> PENDING -> COMMITTED`

or

`ABSENT -> PENDING -> ABORTED`

Enforce these rules during recovery:

1. `transaction_begin` is valid only for an absent transaction ID.
2. `commit` with `transaction_id` is valid only while that transaction is pending.
3. `transaction_commit` is valid only for a pending transaction and consumes it.
4. `transaction_abort` is valid only for a pending transaction and consumes it.
5. Terminal transitions for unknown IDs fail closed.
6. A transaction ID cannot be reopened after a terminal transition during the same replay.

This step deliberately does **not** cross-check `transaction_commit.object_ids` against staged commit records. That is a separate integrity question and should not be conflated with lifecycle-state validation without additional evidence about the field's intended authority.

## Consequence

Malformed durable transaction order can no longer silently change the recovered state machine. Existing valid crash/restart semantics remain unchanged, while duplicate/out-of-order lifecycle records become explicit journal corruption.

## What remains unproven

This reconnaissance does not establish crash consistency of arbitrary host filesystems beyond the journal's existing fsync/EOF-tail behavior, nor does it qualify multi-process transaction concurrency beyond the existing storage coordination mechanisms. The `object_ids` semantic binding remains a separate review item.
