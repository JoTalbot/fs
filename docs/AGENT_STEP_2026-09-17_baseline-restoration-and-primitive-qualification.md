# Agent step 2026-09-17 — baseline restoration, defect repair, primitive qualification

- agent_id: `arena-01a0af2b-fs`
- environment: arena.ai agent mode sandbox (Linux, Python 3.11.2, `gh` as `arena-ai-coding-agent[bot]`)
- base_commit: `49e53b3efb144974438b9cce25fcaff7c2624ef6` (shallow clone, depth 1)
- area: repository baseline, CLI, storage/state primitives, roadmap evidence, coordination substrate
- claimed_files: `src/fs_overlay/policy.py`, `src/fs_overlay/cli.py`, `tests/test_policy.py`, `tests/test_package_import_surface.py`, `tests/test_storage_transaction_recovery.py`, `tests/test_cli.py`, `tests/test_state_primitives.py`, `tests/test_storage_primitives.py`, `tools/roadmap_evidence.py`, `tests/test_roadmap_evidence.py`, `docs/ROADMAP.md`, `docs/TASK-PROTOCOL.md`, `docs/AUTONOMOUS-DEVELOPMENT-MASTER.md`, `docs/M0.md`, `docs/PRODUCT-DECISIONS.md`, `agent/state/current.yml`, `.gitignore`

## Research

- Repository: read `AGENTS.md`, `AGENT_STATUS.md`, `AGENT_LOG.md`,
  `docs/ROADMAP.md`, `docs/ROADMAP_V1.md`, `docs/V1_RELEASE_GATE.md`,
  `.github/workflows/*.yml`, `pyproject.toml`, and the source modules touched.
- Requested-but-absent files: `docs/AUTONOMOUS-DEVELOPMENT-MASTER.md`,
  `docs/TASK-PROTOCOL.md`, `docs/M0.md`, `docs/PRODUCT-DECISIONS.md` and
  `agent/state/current.yml` did not exist in this repository. The existing
  coordination surface was `AGENT_STATUS.md` + `AGENT_LOG.md` +
  `.agents/skills/fs-agent-core/SKILL.md`; the new files extend it rather than
  replace it (recorded as PD-006).
- Measurement instead of assumption: `coverage.py --source=src` produced the
  first per-module coverage baseline for this work (85% -> 88% total), and
  `pkgutil.iter_modules` produced the import-surface census (85 modules, 1
  unimportable).
- Skill discovery: the canonical local skill `.agents/skills/fs-agent-core`
  applies; no external skill was adopted and none was allowed to override the
  repository contract.

## Findings (all observed, not inferred)

1. `src/fs_overlay/policy.py` raised `SyntaxError: '(' was never closed` at line
   19. 84 of 85 modules imported; this one did not, and nothing imported it, so
   the ordinary matrix stayed green while a broken module shipped.
2. `CarrierPolicy.denied_names` was unreachable: a file named exactly `id_rsa`
   or `.ssh` has no suffix and can never satisfy `allowed_suffixes`, so the deny
   list could not reject `.ssh/id_rsa.log` under an allowed root.
3. `fs-overlay genesis ... --admit` sent `{"operation": "admit"}` through the
   request handler. `GenesisService` rejects that operation by design
   (`tests/test_genesis_service.py` asserts `unsupported operation: admit`), so
   the flag always exited 1 - observed before the fix.
4. `--metadata bogus` produced an uncaught `ValueError` traceback with exit 1
   instead of a structured usage error.
5. `tests/test_storage_transaction_recovery.py` child processes failed with
   `ModuleNotFoundError` in a src-layout checkout (3 failures) because they
   inherited no `PYTHONPATH`; CI passed only because it installs the package.
6. `src/fs_overlay/cli.py` was at 21% coverage and had no dedicated test file.
7. Thirteen primitives claimed by the roadmap were never referenced by name in
   any test file.
8. The repository had no `.gitignore`.
9. `gh workflow run release-provenance.yml --repo JoTalbot/fs --ref main`
   returned `HTTP 403 Resource not accessible by integration`
   (`/actions/workflows/360042142/dispatches`), confirming issues #15 and #16.

## Changes

- Repaired `fs_overlay/policy.py`, made the deny list component-wise
  (fail-closed), and added `tests/test_policy.py`.
- Added `tests/test_package_import_surface.py`: every packaged module must parse
  and import.
- Repaired the CLI admission path (local configuration, not transport) and
  argument-error reporting (structured JSON, exit 2); added `tests/test_cli.py`.
- Made crash/restart child processes hermetic via `PYTHONPATH`.
- Added `tests/test_state_primitives.py` and `tests/test_storage_primitives.py`.
- Added `tools/roadmap_evidence.py` + `tests/test_roadmap_evidence.py`, and
  reconciled 33 roadmap items against that registry.
- Added the coordination substrate: `agent/state/current.yml`,
  `docs/TASK-PROTOCOL.md`, `docs/AUTONOMOUS-DEVELOPMENT-MASTER.md`,
  `docs/M0.md`, `docs/PRODUCT-DECISIONS.md`, and `.gitignore`.

## Validation actually performed

- `.venv/bin/python -m pytest`: **842 passed, 3 skipped, 14 deselected**
  (Python 3.11.2). Before this session's changes on the same tree: 576 passed
  and 3 failed without an installed package.
- `.venv/bin/python -m coverage run --source=src -m pytest` +
  `coverage report`: total **88%**; `state_primitives.py` 63% -> 100%,
  `storage_engine.py` -> 94%, `cli.py` 21% -> 88%, `policy.py` -> 96%.
- `.venv/bin/python tools/roadmap_evidence.py`: **33 items verified**.
- `.venv/bin/python tools/independent_conformance_consumer.py`: PASS (2 canonical
  vectors, 1 admission vector delegated).
- `.venv/bin/python tools/independent_admission_conformance.py`: PASS (10
  admission-negative cases).
- Observed CLI behaviour after the fix: `genesis ping` -> `ready: false`,
  `genesis ping --admit` -> `ready: true` (exit 0), malformed metadata ->
  structured error on stderr with exit 2.
- Not executed here: the 18-job GitHub CI matrix (branch pushed; a pull request
  is required to trigger it) and the release-provenance workflow (403).

## Unresolved / next

- M0-07: open a pull request so ordinary CI and the OSV gate run against this
  batch, then record the run IDs.
- M2-01/M2-02 remain blocked on human-only evidence (workflow dispatch
  permission; audited AEAD, key store and transport qualification).
- M3-01: weakest modules remain `production_crypto.py` 37%, `windows_job.py`
  41%, `freebsd_capsicum.py` 53%, `workspace_boundary.py` 56%.

## Durable learning

- [FAILURE] A packaged module can be unimportable while the whole matrix is
  green. The import surface itself must be a tested contract.
- [RULE] Roadmap checkboxes are claims; bind each claim to modules, symbols and
  tests, and check it mechanically.
- [SECURITY] A deny list that can never match is worse than none, because it
  reads as protection. Verify reachability of safety branches.
- [SECURITY] Admission must never be grantable through a request transport; a CLI
  flag that tries is a broken control surface, not a convenience.
- [TOOLING] The host interpreter rejects pip installs (PEP 668); use a venv with
  an editable install so tests mirror CI.
- [FAILURE] Tests that spawn interpreters must export `PYTHONPATH`; otherwise
  they pass in CI and fail in a source checkout, or vice versa.
