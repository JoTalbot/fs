# Agent step: workspace content-addressed state

Date: 2026-09-15
Agent: `gpt-5.6-luna`
Repository: `JoTalbot/fs`

## Goal

Advance Phase 3 from logical workspace registration toward immutable, content-addressed workspace state without introducing a second snapshot format or mutating host paths.

## Findings

- `SnapshotStore` already provides immutable snapshot records, deterministic object ordering, content-derived identity, and Merkle verification.
- `LocalStorageEngine` exposes the durable inventory of content-addressed objects.
- Workspace admission is already fail-closed and rejects symlink roots.

## Changes

Added `src/fs_overlay/workspace_state.py`:

- `WorkspaceState` binds a logical `workspace_id` to an existing verified `Snapshot`.
- `WorkspaceStateStore` reuses `SnapshotStore` rather than creating a parallel snapshot format.
- Snapshot metadata carries the workspace identity and explicit observed/managed mode.
- Cross-workspace retrieval is rejected by metadata verification.
- Caller-supplied conflicting `workspace_id` metadata is rejected.
- `create_registered()` resolves the binding from `WorkspaceRegistry`.
- Missing or invalid workspace paths fail through the existing admission boundary.
- No method creates, mounts, copies, deletes, or changes permissions on the host workspace.

Added `tests/test_workspace_state.py` covering identity binding, cross-workspace rejection, metadata override rejection, registry integration, and no-host-mutation behavior.

## Commits

- `f59cf8c7a2c3e37ab28ea8678434f99958e82537` — workspace content-addressed state implementation.
- `533d2ed21fc307b9fd942c7e9a3e01c5e1ce3ac9` — workspace state regression tests.

## Validation boundary

No local checkout or test runner is available in this session. GitHub Actions is the authoritative validation boundary. The prior registry/isolation matrix had passed, while the latest workspace-state commits require their own CI result to be observed before claiming a pass.

## Architectural decision

Workspace state is a logical catalog view over immutable storage objects. It is not a filesystem copy and does not imply recovery authority. Future import/export and rollback work must preserve this distinction and require explicit ownership/delegation plus verification before any host mutation.

## Next

Observe CI for this step. Then continue Phase 3 with explicit migration/import/export plans, followed by verified snapshot/recovery transitions. Avoid implementing destructive import or rollback until their authority and recovery boundaries are explicit.
