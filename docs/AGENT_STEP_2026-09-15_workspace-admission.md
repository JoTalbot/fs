# Agent step: workspace admission boundary

Date: 2026-09-15
Agent: `gpt-5.6-luna`
Repository: `JoTalbot/fs`

## Goal

Close the workspace-root identity gap discovered during isolation qualification. Every workspace admission path must reject ambiguous symlink roots before a mount or execution plan is produced.

## Change

- `src/fs_overlay/workspace.py` now rejects a supplied workspace root when the path itself is a symlink.
- Rejection reason: `workspace_path_must_not_be_symlink`.
- `tests/test_workspace.py` now verifies the common workspace admission path fails closed for a real directory plus symlink alias.

This generalizes the earlier Bubblewrap-specific guard so `plan_workspace()` and downstream mount-namespace planning share the same boundary rule. The change is additive and does not broaden authority or mutate host state.

## Validation

The repository CI workflow is configured for pushes to `main` across Ubuntu, Windows, and macOS with Python 3.11, 3.12, and 3.13, plus the crypto-provider matrix. The two new commits triggered CI runs 416 and 417, both observed queued at inspection time. No passing result is claimed yet.

The connector session has no local checkout/test runner, so local pytest execution is unavailable here.

## Result

- `f3b4b5326f3fec55b0415730da2c37aef7e690fd` — reject symlink workspace roots during common workspace admission.
- `e2ef47da6d434e477336d9521e44869070516ae9` — add common workspace-admission regression coverage.

## Learning

- [SECURITY] The isolation-root invariant belongs at the earliest common admission boundary, not only in one execution backend.
- [RULE] A downstream backend must not be responsible for repairing an ambiguity that upstream workspace admission can reject deterministically.
- [VALIDATION] CI execution evidence is required before treating the new head as qualified; queued is not passed.

## Next

1. Inspect CI run 417/416 results and fix any regression without weakening the fail-closed rule.
2. Continue Phase 3 workspace registration, health, import/export and content-addressed state using existing abstractions.
3. Continue explicit journal/crash and workspace recovery qualification.
4. Preserve production security blockers and the distinction between capability detection and authority.
