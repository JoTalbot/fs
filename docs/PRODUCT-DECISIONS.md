# Product Decisions

This log records durable product-level decisions for `JoTalbot/fs`, including
decisions that were deferred or rejected. Architectural invariants live in
`docs/CONSTITUTION.md`; compatibility rules live in `docs/COMPATIBILITY.md`.
This file records the decisions themselves, with the evidence that produced them,
so a later agent does not re-litigate them.

Format: `id | status | decision | evidence/consequence`.
Statuses: `ACCEPTED`, `DEFERRED`, `REJECTED`.

## Engineering and process decisions

- **PD-001 | ACCEPTED | Roadmap completion claims must be evidence-bound.**
  A checked roadmap item names the modules, top-level symbols and test files that
  back it, registered in `tools/roadmap_evidence.py` and enforced by
  `tests/test_roadmap_evidence.py`. Consequence: 33 claims were reconciled;
  claims without registry entries are explicitly marked unreconciled rather than
  silently assumed.

- **PD-002 | ACCEPTED | The package import surface is a tested contract.**
  Every module shipped in the sdist/wheel must parse and import. Evidence:
  `fs_overlay/policy.py` shipped with an unclosed parenthesis and raised
  `SyntaxError`, undetected because no test imported it. Consequence:
  `tests/test_package_import_surface.py`.

- **PD-003 | ACCEPTED | CLI admission is local configuration, never a transport
  request.** `fs-overlay genesis --admit` builds the local service with
  `admitted=True`. `GenesisService` rejects `admit` over the request path by
  design, so a request-based flag could only ever fail closed. Consequence:
  `tests/test_cli.py` pins both the working local path and the rejected
  transport path.

- **PD-004 | ACCEPTED | Safety deny lists apply to every path component.**
  `CarrierPolicy` rejects a path when any component is denied. Comparing only
  the file name made the deny list unreachable, because a name such as `id_rsa`
  has no suffix and could never match the allow list. Consequence:
  `.ssh/id_rsa.log` under an allowed root is now rejected.

- **PD-005 | ACCEPTED | Tests must not depend on an installed distribution.**
  Child processes spawned by tests receive `PYTHONPATH` pointing at `src`.
  Evidence: three crash/restart qualification tests failed in a plain src-layout
  checkout with `ModuleNotFoundError: No module named 'fs_overlay'` while CI
  passed because CI installs the package.

- **PD-006 | ACCEPTED | Coordination artifacts are additive.**
  `agent/state/current.yml` and `docs/TASK-PROTOCOL.md` extend the
  `AGENTS.md` protocol; they do not replace `AGENT_STATUS.md` or `AGENT_LOG.md`,
  which remain the shared human-readable surface required by the contract.

## Product and security decisions

- **PD-007 | ACCEPTED | The HMAC envelope provides integrity only.**
  `HMACIntegrityEnvelope` is a development envelope and must never be described
  as confidential. Consequence: a test asserts the plaintext is visible in the
  ciphertext, so a future "encryption" rename cannot pass silently.

- **PD-008 | ACCEPTED | No production security claim without external
  qualification.** The V1 gate keeps "production confidentiality provider is an
  audited AEAD implementation" unchecked until an audited provider, a qualified
  secure key store and an authenticated transport adapter each have their own
  evidence. Repository work cannot self-certify this.

- **PD-009 | ACCEPTED | Release provenance stays open until observed.**
  `.github/workflows/release-provenance.yml` is implemented with pre-attestation
  validation and mandatory post-attestation verification, but the gate item
  requires an observed execution with verified wheel/sdist/SBOM attestations.
  Evidence of the current limitation: `gh workflow run` returned
  `HTTP 403 Resource not accessible by integration` for workflow id
  `360042142`.

- **PD-010 | ACCEPTED | Erasure coding ships as an interface only.**
  `ErasureCoder` is a protocol; no production coder is shipped or claimed. The
  Phase 5 item "Reed-Solomon implementation or audited dependency" remains open
  rather than being satisfied by an unaudited dependency.

## Deferred and rejected

- **PD-011 | REJECTED | GitHub Dependency Review as a PR gate.** The repository
  has Dependency Graph disabled, so the action failed with "Dependency review is
  not supported on this repository". Leaving an always-failing workflow on `main`
  would create a deterministic red check. OSV-Scanner was adopted instead
  (`.github/workflows/osv-scanner.yml`).

- **PD-012 | DEFERRED | FreeBSD native CI.** `.cirrus.yml` intentionally runs no
  native FreeBSD jobs; the capsicum tests skip outside a real FreeBSD kernel.
  Revisit only when a FreeBSD runner is available and the isolation claim can be
  evidenced.

- **PD-013 | DEFERRED | Merging the session branch into `main` by an agent.**
  Autonomous batches push their own branch and open a pull request for CI
  evidence; the merge decision stays with the maintainer.
