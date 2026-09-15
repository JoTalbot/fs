# Agent step: transfer journal concurrency

Date: 2026-09-15

## Change

`WorkspaceTransferJournal` now serializes every state-dependent append with the existing cross-process `FileAdmissionCoordinator`.

- `begin()` holds the journal lock while deriving `previous_digest` and appending the prepared record.
- `mark()` holds the same lock across replay, transaction identity validation, transition validation, and append.
- Hash-chain construction therefore cannot race between independent processes.
- A concurrent transition against the same transaction is re-evaluated after the first writer commits, so only one valid state transition is accepted.
- The lock is retained as a sidecar path under `.journal-locks`; no stale-lock deletion or lock stealing is introduced.

## Qualification

Multiprocessing tests use Python's `spawn` context and independent journal instances against the same path. They verify:

1. concurrent `begin()` calls preserve both transactions and the complete SHA-256 chain;
2. concurrent `mark(..., MATERIALIZING)` calls against one transaction produce exactly one successful transition and one fail-closed invalid-transition result.

Host filesystem mutation remains disabled. This step changes only durable journal coordination and evidence; it does not grant execution authority.
