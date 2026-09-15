# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Latest implementation head: `e2ef47da6d434e477336d9521e44869070516ae9`
- Latest status/handoff commit: `0029d3e7aaaf550f8164c5ae2423281156ce199d`
- Updated: 2026-09-15

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: workspace admission and filesystem isolation boundary qualification
- claimed_files: `src/fs_overlay/workspace.py`, `tests/test_workspace.py`, `docs/AGENT_STEP_2026-09-15_workspace-admission.md`, `AGENT_STATUS.md`
- goal: enforce one deterministic fail-closed workspace-root invariant across all admission and downstream isolation paths
- status: common workspace admission now rejects symlink roots; regression coverage and durable handoff are recorded; CI runs 416 and 417 were observed queued
- decision: workspace roots must have unambiguous filesystem identity before admission or isolation planning
- next_step: inspect CI results, fix only evidence-backed regressions, then continue Phase 3 workspace registration/health/import-export and explicit journal/crash recovery qualification

## Latest work

- `f3b4b5326f3fec55b0415730da2c37aef7e690fd` — common workspace admission rejects symlink roots with `workspace_path_must_not_be_symlink`.
- `e2ef47da6d434e477336d9521e44869070516ae9` — regression coverage for symlink workspace admission.
- `0029d3e7aaaf550f8164c5ae2423281156ce199d` — durable workspace-admission handoff.
- Earlier Bubblewrap-specific symlink protection remains in place; the common admission invariant now prevents downstream divergence.

## Validation boundary

CI workflow covers Ubuntu, Windows and macOS with Python 3.11, 3.12 and 3.13, plus the crypto-provider matrix. Runs 416 and 417 were queued when inspected. No CI pass is claimed until a completed successful run is observed. This session has no local checkout/test runner.

## Current V1 position

V1 is **not** production-ready. Candidate AES-GCM qualification is behavioral evidence only. Production still requires a real audited AEAD, secure key storage/lifecycle, authenticated/encrypted transport, target-specific recovery evidence, and required external security review.

FreeBSD native CI remains intentionally disabled and outside the release gate.

## Existing architecture boundary

Preserve fail-closed isolation, explicit authority, evidence-before-commit, no secret material in repository state, and the distinction between capability detection and granted authority. Existing foundation includes trust/capabilities, federation envelopes and replay/admission, cross-process coordination, replica/self-healing, deterministic negotiation, key lifecycle admission, conformance validation, execution/recovery primitives, and explicit workspace/network isolation contracts.

## Next phase

1. Validate the corrected workspace/isolation head through the full CI matrix.
2. Continue Phase 3 workspace registration, health, import/export and content-addressed state where existing abstractions support it.
3. Continue Phase 2/5 explicit journal/crash and workspace recovery qualification.
4. Keep the production security gate blocked until concrete audited deployment evidence exists.
