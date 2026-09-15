# Agent step: workspace migration boundaries

Date: 2026-09-15
Agent: `gpt-5.6-luna`
Repository: `JoTalbot/fs`

## Goal

Advance Phase 3 from immutable workspace state to explicit migration/import/export planning without performing host filesystem mutation.

## Research

Repository reconnaissance found no existing migration/import/export implementation to reuse. Existing `WorkspaceBinding`, `WorkspaceRegistry`, `WorkspaceStateStore`, `SnapshotStore`, and Merkle verification provide the required authority and state boundaries.

Python filesystem documentation was checked before defining the boundary. Host filesystem replacement/move operations can overwrite existing destinations, so this step deliberately stops at a verified plan and does not invoke copy, replace, move, delete, or rollback operations.

## Decision

question -> sources -> findings -> decision -> consequence -> remaining uncertainty

- question: how should workspace migration begin safely?
- sources: existing FS workspace/state abstractions; current Python filesystem semantics.
- findings: workspace identity and ownership are already explicit; filesystem mutation has destructive semantics and must not be conflated with logical state transfer.
- decision: implement plan-only export/import/migrate contracts. Export preserves source. Import requires an existing, explicitly owned/delegated, writable destination and an empty destination. Migration requires distinct source/destination identities. Registered migration requires a managed destination.
- consequence: callers receive deterministic readiness/reason codes before any future execution layer is allowed to mutate host state.
- remaining uncertainty: actual materialization, overwrite/merge policy, rollback journal, and cross-host transfer protocol require a separate authority-bearing implementation and qualification step.

## Changes

Added `src/fs_overlay/workspace_migration.py`:

- `WorkspaceTransfer` operation enum for export/import/migrate.
- immutable `WorkspaceTransferPlan` with readiness, explicit non-destructive/source-preserved semantics, and `destination_must_be_empty` policy.
- `plan_export()` validates source identity and admission.
- `plan_import()` validates destination admission, ownership/delegation, writability, and empty-destination preflight.
- `plan_migration()` composes export/import checks and rejects same-workspace migration.
- `plan_registered_migration()` resolves source/destination through the registry and requires managed destination mode.
- no function copies, moves, deletes, mounts, replaces, or changes permissions on host paths.

Added regression coverage for a non-empty destination safe-stop. The migration tests now cover ready plans, identity mismatch, non-empty/read-only destinations, distinct migration identities, and registry managed-mode enforcement.

## Validation boundary

No local checkout/test runner is available. GitHub Actions remains authoritative. Run 432 (`34941144863`) completed successfully across the observed Python 3.11/3.12/3.13 and crypto-provider matrix. The subsequent conflict-preflight commits have triggered a fresh CI run and require their own result before a pass is claimed.

## Learning

- `RULE`: logical transfer planning must not imply filesystem mutation authority.
- `SECURITY`: destination ownership/delegation, writability, and conflict policy are explicit preconditions for import planning.
- `ARCHITECTURE`: an import has no host source path; its source is a verified immutable snapshot, so the plan keeps `source_path=None` rather than inventing a filesystem claim.
- `SAFETY`: defaulting to reject non-empty destinations avoids implicit overwrite/merge semantics until a future executor has explicit authority and rollback evidence.

## Commits

- `96b2aa7842f7cf1b2020f4d703461db041c9dbca` — initial plan-only migration boundary.
- `a9dfc0c20d65d5c57ee1765c2e7c21cb8df203b4` — remove host-path claim from logical import source.
- `b3119e62a4cdcd3fb34b25fe3e2ff43fda6e4ad8` — migration tests.
- `6c45532db1775c06a60cb23986cc6b6353c37066` — correct migration regression tests.
- `204a68f083394c9ea99c649e6880238c...` — explicit destination conflict preflight and unused-import cleanup.
- `f00e730681898ae013a8f60b74b971e400f2f6d9` — regression test for non-empty destination safe-stop.

## Next

Observe the fresh CI run. If clean, proceed to an authority-bearing transfer executor design with explicit destination conflict policy, transactional journal boundaries, crash recovery, and rollback evidence. Do not implement destructive host mutation before those controls exist.
