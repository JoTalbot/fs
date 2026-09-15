# FS Agent Status

> Shared coordination state for parallel AI agents.

## Current repository

- Repository: `JoTalbot/fs`
- Branch: `main`
- Current commit: `023d0fa986241684339ee50920aab6114a245501`
- Updated: 2026-09-15

## Active step

- agent_id: `gpt-5.6-luna`
- machine_id: `GitHub connector`
- area: workspace filesystem isolation boundary qualification
- claimed_files: `src/fs_overlay/isolation.py`, `tests/test_isolation.py`, `AGENT_STATUS.md`, `docs/AGENT_STEP_2026-09-15_workspace-isolation.md`
- goal: strengthen the explicit workspace-only execution boundary without changing the released preview behavior, while preserving fail-closed semantics
- status: workspace root symlink escape is now rejected before bubblewrap planning; deterministic regression coverage and durable step handoff are recorded
- decision: a workspace supplied through a symlink is not accepted as an isolation root because the configured path and the mounted filesystem identity can otherwise diverge
- next_step: qualify the corrected isolation head through CI/full test matrix, then continue workspace registration/import and explicit journal/crash qualification

## Latest work

- `52f4b1bb13fca1e6bb6cde818ff3cccef318778e`: rejected symlink workspace roots in `BubblewrapWorkspaceBackend.plan()` before constructing an isolation plan.
- `dff98ccd2bacf2b2ecdd6872faf1dc0210e5dcde`: added a regression proving symlink workspace roots fail closed with `workspace_path_must_not_be_symlink`.
- `023d0fa986241684339ee50920aab6114a245501`: recorded the durable workspace-isolation handoff in `docs/AGENT_STEP_2026-09-15_workspace-isolation.md` and synchronized this status.
- Existing bubblewrap workspace enforcement remains explicit: workspace is mounted at `/workspace`, only declared runtime roots are exposed, and denied networking uses an explicit network namespace boundary.
- Existing Linux namespace backend remains a separate capability mechanism and is not treated as workspace filesystem isolation evidence.

## Validation boundary

The GitHub connector can inspect repository state but this session has no local checkout/test runner. No local test pass or CI pass is claimed for the new isolation head. CI/full-matrix validation is the next gate.

## Current V1 position

V1 is **not** production-ready. Candidate AES-GCM qualification is behavioral evidence only. Production still requires a real audited AEAD, secure key storage/lifecycle, authenticated/encrypted transport, target-specific recovery evidence, and required external security review.

FreeBSD native CI remains intentionally disabled and outside the release gate.

## Existing architecture boundary

The completed foundation includes node identity/trust, signed capabilities, canonical federation envelopes, durable replay/admission state, cross-process coordination adapters, replica/self-healing primitives, deterministic negotiation, key lifecycle admission, conformance vectors/validators, MinimalInitiator, explicit production adapter contracts, EventLog recovery/concurrency qualification, transaction crash/recovery qualification, failure-domain-aware replica recovery, deterministic two-node/three-node federation-state fixtures, and explicit workspace/network isolation contracts. Preserve fail-closed isolation, explicit authority, evidence-before-commit, and no secret material in repository state.

## Release-readiness boundary

The semantic V1 release gate remains blocked on deployment-specific security evidence:

1. real audited AEAD for the exact deployment;
2. secure key lifecycle storage with access control, rotation, revocation, backup/recovery and audit evidence;
3. authenticated/encrypted transport with explicit trust/revocation policy;
4. target-specific qualification and operational recovery evidence;
5. exact provider versions/configuration and external security-review evidence in `docs/PRODUCTION_QUALIFICATION_RECORD.md`.

## Next phase

- Validate corrected isolation head `023d0fa986241684339ee50920aab6114a245501` across the full matrix.
- Continue Phase 3 with workspace registration, health, import/export and content-addressed workspace state where existing abstractions support it.
- Continue Phase 2/5 with explicit journal/crash and workspace recovery boundaries.
- Preserve the distinction between process-local synchronization and cross-process durable coordination.
- Keep V1 blocked until concrete production evidence exists.
