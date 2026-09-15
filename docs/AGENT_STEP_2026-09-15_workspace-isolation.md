# Agent step: workspace isolation boundary

Date: 2026-09-15
Agent: `gpt-5.6-luna`
Repository: `JoTalbot/fs`

## Goal

Continue the filesystem/workspace isolation block without changing the released preview behavior. The isolation boundary must fail closed when the configured workspace root can be ambiguous with another filesystem location.

## Research

- `src/fs_overlay/isolation.py` already uses an explicit Bubblewrap workspace backend for `workspace-only` execution.
- The backend mounts the configured workspace at `/workspace`, exposes only explicit runtime roots, and treats denied networking as a separate observable namespace guarantee.
- Linux namespace capability is intentionally not treated as proof of workspace filesystem isolation.
- Repository coordination requires durable state in `AGENT_STATUS.md` and append-only learning records rather than private chat state.

## Change

- `BubblewrapWorkspaceBackend.plan()` now rejects a workspace root when the supplied path itself is a symlink.
- Rejection reason: `workspace_path_must_not_be_symlink`.
- This prevents the configured workspace identity from diverging from the actual directory mounted by the isolation backend.
- Added a deterministic regression test creating a real directory plus a symlink alias and requiring fail-closed planning.

## Validation boundary

The GitHub connector can inspect repository state and commits, but this session does not have a local checkout/test runner. Therefore no local test pass or CI pass is claimed here. The new head must be validated by the repository CI matrix before this step is considered fully qualified.

## Result

Implementation commits:

- `52f4b1bb13fca1e6bb6cde818ff3cccef318778e` — reject symlink workspace roots.
- `dff98ccd2bacf2b2ecdd6872faf1dc0210e5dcde` — add symlink-boundary regression.
- `54f09c0c222dbdc9e4726539318b0b4461cf5c4d` — synchronize shared agent status.

## Learning

- [SECURITY] A path used as an isolation root must have an unambiguous filesystem identity before the backend constructs its mount plan.
- [RULE] Capability detection and isolation planning are not execution evidence; CI/runtime qualification remains required.
- [PROCESS] Keep the released preview path unchanged and make new enforcement additive, explicit, and fail-closed.

## Next

1. Validate the new head through the full CI matrix.
2. Continue Phase 3 workspace registration/import/export and health semantics where existing abstractions permit.
3. Continue explicit journal/crash and workspace recovery qualification.
4. Keep production security blocked until concrete audited providers and deployment evidence exist.
