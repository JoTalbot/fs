# Agent step: workspace migration boundaries

Date: 2026-09-15
Agent: `gpt-5.6-luna`
Repository: `JoTalbot/fs`

## Goal

Advance Phase 3 from immutable workspace state to explicit migration/import/export planning and a durable transaction-intent boundary without performing host filesystem mutation.

## Decision

Transfer remains split into a verified plan, explicit authority, durable intent journal, and a future authority-bearing materializer. Runtime capability never expands authority.

The journal now uses a closed state machine:

- `prepared -> materializing`
- `prepared -> aborted`
- `materializing -> committed`
- `materializing -> aborted`
- `committed` and `aborted` are terminal.

Every later record must preserve the transaction's operation, snapshot, source workspace, and destination workspace identity. Replay fails closed on identity changes, illegal transitions, unsupported phases, unsupported versions, and malformed non-tail records. A truncated final EOF record remains the only tolerated incomplete append.

A transaction ending in `materializing` is exposed as a recovery candidate. It is never auto-committed, and journal presence never grants filesystem mutation authority.

## Changes

`src/fs_overlay/workspace_migration.py` provides the plan-only export/import/migrate boundary with explicit destination preflight and no host filesystem mutation.

`src/fs_overlay/workspace_transfer_authority.py` provides explicit approved authority bound to transaction, snapshot, workspace identities and operation-specific scope.

`src/fs_overlay/workspace_transfer_journal.py` now provides:

- `TransferJournalPhase` with prepared/materializing/committed/aborted states.
- transition validation and terminal-state enforcement.
- transaction identity continuity checks during append and replay.
- reopen-safe continuation of valid transactions.
- `recovery_candidates()` for unresolved materializing transactions.
- append-only records with flush + fsync.

`tests/test_workspace_transfer_journal.py` covers invalid transitions, terminal-state rejection, unknown transactions, identity changes, reopen/continuation, recovery candidates, replay corruption, incomplete EOF tolerance, and malformed non-tail records.

## Validation boundary

No local checkout/test runner is available. GitHub Actions remains authoritative. Earlier full matrices passed, but the journal state-machine commits require the fresh CI result before a pass is claimed.

## Learning

- `RULE`: logical transfer planning must not imply filesystem mutation authority.
- `SECURITY`: explicit authority is separate from capability detection, ownership, and path access.
- `ARCHITECTURE`: an import source is a verified immutable snapshot, not an inferred host path.
- `RECOVERY`: an interrupted `materializing` transaction is unresolved state, not evidence of success.
- `SAFETY`: source preservation remains mandatory in the plan; source deletion and destination replacement are outside this journal's authority.

## Commits

- `96b2aa7842f7cf1b2020f4d703461db041c9dbca` — initial plan-only migration boundary.
- `a9dfc0c20d65d5c57ee1765c2e7c21cb8df203b4` — logical import source semantics.
- `6c45532db1775c06a60cb23986cc6b6353c37066` — migration regression coverage.
- `204a68f083394c9ea99c649e688023238ca8d7a2d3` — destination conflict preflight.
- `f00e730681898ae013a8f60b74b971e400f2f6d9` — non-empty destination regression test.
- `dec125383700fab1a33893b5156b6fdef2d7349e` — durable transfer journal boundary.
- `5cf4b519687406b4f458c62f54b15e6a3f9244a7` — journal replay/corruption regression tests.
- `1e1f239768f6300647d1b3d7b5fcdab2e1a7916a` — enforce journal state machine and identity continuity.
- `51a82437130e1562115a106f4bad7a8a9fddd390` — journal recovery regression coverage.

## Next

Observe fresh CI. If clean, define a non-destructive materializer protocol around explicit authority + journal state, then add crash reconciliation and rollback evidence. Do not implement destructive host mutation until those controls are qualified.
