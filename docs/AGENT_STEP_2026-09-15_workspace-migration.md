# Agent step: workspace migration boundaries

Date: 2026-09-15
Agent: `gpt-5.6-luna`
Repository: `JoTalbot/fs`

## Goal

Advance Phase 3 from immutable workspace state to explicit migration/import/export planning without performing host filesystem mutation.

## Research

Repository reconnaissance found no existing migration/import/export implementation to reuse. Existing `WorkspaceBinding`, `WorkspaceRegistry`, `WorkspaceStateStore`, `SnapshotStore`, and Merkle verification provide the required authority and state boundaries.

Python filesystem documentation was checked before defining the boundary. Host filesystem replacement/move operations can overwrite existing destinations, so this step deliberately stops at a verified plan and does not invoke copy, replace, move, delete, or rollback operations. citeturn1search2turn1search5

## Decision

question -> sources -> findings -> decision -> consequence -> remaining uncertainty

- question: how should workspace migration begin safely?
- sources: existing FS workspace/state abstractions; current Python filesystem semantics.
- findings: workspace identity and ownership are already explicit; filesystem mutation has destructive semantics and must not be conflated with logical state transfer.
- decision: implement plan-only export/import/migrate contracts. Export preserves source. Import requires an existing, explicitly owned/delegated, writable destination. Migration requires distinct source/destination identities. Registered migration requires a managed destination.
- consequence: callers receive deterministic readiness/reason codes before any future execution layer is allowed to mutate host state.
- remaining uncertainty: actual materialization, destination conflict policy, rollback journal, and cross-host transfer protocol require a separate authority-bearing implementation and qualification step.

## Changes

Added `src/fs_overlay/workspace_migration.py`:

- `WorkspaceTransfer` operation enum for export/import/migrate.
- immutable `WorkspaceTransferPlan` with readiness and explicit non-destructive/source-preserved semantics.
- `plan_export()` validates source identity and admission.
- `plan_import()` validates destination admission, ownership/delegation, and writability.
- `plan_migration()` composes export/import checks and rejects same-workspace migration.
- `plan_registered_migration()` resolves source/destination through the registry and requires managed destination mode.
- no function copies, moves, deletes, mounts, replaces, or changes permissions on host paths.

Added `tests/test_workspace_migration.py` covering ready plans, identity mismatch, read-only destination, distinct migration identities, and registry managed-mode enforcement.

## Validation boundary

No local checkout/test runner is available. GitHub Actions remains authoritative. Run 426 for the workspace-state/status correction completed successfully across the observed Python and crypto matrix. The new migration commits require their own CI run before a pass is claimed.

## Learning

- `RULE`: logical transfer planning must not imply filesystem mutation authority.
- `SECURITY`: destination ownership/delegation and writability are explicit preconditions for import planning.
- `ARCHITECTURE`: an import has no host source path; its source is a verified immutable snapshot, so the plan keeps `source_path=None` rather than inventing a filesystem claim.

## Commits

- `96b2aa7842f7cf1b2020f4d703461db041c9dbca` — initial plan-only migration boundary.
- `a9dfc0c20d65d5c57ee1765c2e7c21cb8df203b4` — remove host-path claim from logical import source.
- `b3119e62a4cdcd3fb34b25fe3e2ff43fda6e4ad8` — migration tests.
- `6c45532db1775c06a60cb23986cc6b6353c37066` — correct migration regression tests.

## Next

Observe migration CI. If clean, implement verified destination conflict/preflight semantics before any actual import/export executor. Keep destructive move and rollback out of scope until authority and recovery journaling are explicit.
