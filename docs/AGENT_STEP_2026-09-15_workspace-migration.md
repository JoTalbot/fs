# Agent step: workspace migration boundaries

Date: 2026-09-15
Agent: `gpt-5.6-luna`
Repository: `JoTalbot/fs`

## Goal

Advance Phase 3 from immutable workspace state to explicit migration/import/export planning and a durable transaction-intent boundary without performing host filesystem mutation.

## Research

Repository reconnaissance found no existing workspace transfer executor to reuse. Existing `WorkspaceBinding`, `WorkspaceRegistry`, `WorkspaceStateStore`, `SnapshotStore`, `MerkleDAG`, and the storage journal provide the required authority and durability primitives.

Filesystem replacement/move semantics can be destructive, so transfer remains split into a verified plan, durable intent journal, and a future authority-bearing materializer.

## Decision

question -> sources -> findings -> decision -> consequence -> remaining uncertainty

- question: how should workspace migration become executable without silently gaining host authority?
- sources: existing FS workspace/state abstractions and durable journal patterns.
- findings: identity, ownership, destination conflict policy, and durable transaction state are separate concerns; none should be inferred from runtime capability.
- decision: keep plan-only migration/import/export contracts, reject non-empty destinations by default, then add an append-only transfer journal with explicit `prepared`, caller-defined execution, and `committed` phases. Journal writes require a ready plan and are fsynced.
- consequence: a future materializer has a durable intent boundary and can reconcile interrupted transactions without treating journal presence as permission to mutate a host path.
- remaining uncertainty: actual materialization, authority grant, atomic filesystem commit, crash reconciliation, rollback, and cross-host transfer protocol still require separate implementation and qualification.

## Changes

`src/fs_overlay/workspace_migration.py` now provides:

- `WorkspaceTransfer` operation enum for export/import/migrate.
- immutable `WorkspaceTransferPlan` with readiness, source-preserved semantics, and `destination_must_be_empty` policy.
- source/destination admission, identity, ownership/delegation, writability, managed-mode, and empty-destination preflight.
- no host filesystem mutation.

Added `src/fs_overlay/workspace_transfer_journal.py`:

- immutable `TransferJournalEntry` carrying transaction, operation, snapshot, and workspace identities.
- `WorkspaceTransferJournal.begin()` refuses unready plans and records `prepared` intent durably.
- `mark()` records explicit later phases without granting filesystem authority.
- `replay()` accepts only a truncated final EOF record; malformed non-tail records fail closed.
- journal writes flush and fsync before returning.

Added `tests/test_workspace_transfer_journal.py` covering unready-plan rejection, round-trip phase replay, incomplete EOF tolerance, and malformed non-tail rejection.

## Validation boundary

No local checkout/test runner is available. GitHub Actions remains authoritative. Run 432 (`34941144863`) completed successfully across the observed Python 3.11/3.12/3.13 and crypto-provider matrix. Run 440 (`34941562752`) completed successfully for the status synchronization commit. The journal implementation/tests have triggered a fresh CI run and require its final result before a pass is claimed.

## Learning

- `RULE`: logical transfer planning must not imply filesystem mutation authority.
- `SECURITY`: destination ownership/delegation, writability, managed mode, and conflict policy are explicit preconditions.
- `ARCHITECTURE`: an import has no host source path; its source is a verified immutable snapshot.
- `SAFETY`: the journal records intent and evidence, never authority. Journal presence must never authorize source deletion or destination replacement.
- `RECOVERY`: only an incomplete final EOF record may be treated as an interrupted append; malformed records before later data indicate corruption and must stop replay.

## Commits

- `96b2aa7842f7cf1b2020f4d703461db041c9dbca` — initial plan-only migration boundary.
- `a9dfc0c20d65d5c57ee1765c2e7c21cb8df203b4` — remove host-path claim from logical import source.
- `6c45532db1775c06a60cb23986cc6b6353c37066` — migration regression coverage.
- `204a68f083394c9ea99c649e688023238ca8d7a2d3` — destination conflict preflight and unused-import cleanup.
- `f00e730681898ae013a8f60b74b971e400f2f6d9` — non-empty destination regression test.
- `dec125383700fab1a33893b5156b6fdef2d7349e` — durable transfer journal boundary.
- `5cf4b519687406b4f458c62f54b15e6a3f9244a7` — journal replay/corruption regression tests.

## Next

Observe the fresh CI run. If clean, define explicit authority grants and a materializer protocol, followed by crash-state reconciliation and rollback evidence. Do not implement destructive host mutation until those controls are qualified.
