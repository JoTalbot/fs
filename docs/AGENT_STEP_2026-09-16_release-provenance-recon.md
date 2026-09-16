# Release provenance boundary reconnaissance

Date: 2026-09-16
Repository: `JoTalbot/fs`
Base: `e93a0dc465ffd41753122e7e92bd4d965867e251`

## Scope

Focused review of the release/supply-chain boundary: build workflow, production qualification record, reference deployment profile, signed-release roadmap items, and artifact provenance requirements.

## Research

- GitHub artifact attestations bind releasable artifacts to workflow/repository/commit/event provenance; meaningful security benefit requires verification and signer identity validation. Routine test builds are not the intended target. citeturn0search0turn0search1
- GitHub `actions/attest` requires `id-token: write`, `attestations: write`, and `artifact-metadata: write`; it supports SLSA provenance and CycloneDX/SPDX SBOM attestations. citeturn1search5
- CycloneDX Python 7.3.1 supports reproducible environment SBOM generation with `cyclonedx-py environment`. citeturn2search0turn4search12
- Repository `AGENTS.md` requires fresh repository research, external research, skill discovery, and explicit validation state. fileciteturn98file0

## Repository evidence

- `.github/workflows/ci.yml` contains test and candidate crypto-provider jobs only and did not provide release artifact provenance. fileciteturn100file0
- `pyproject.toml` defines `fs-overlay` version `0.1.0`, setuptools PEP 517 build metadata, and no mandatory runtime dependencies. fileciteturn70file0
- `docs/PRODUCTION_SECURITY_QUALIFICATION.md` requires exact provider/version, dependency/supply-chain review and external security evidence. fileciteturn92file0
- `docs/PRODUCTION_REFERENCE_PROFILE.md` requires exact artifact/commit, provider versions, dependency provenance, qualification commands and audit references, while keeping the production decision `BLOCKED` until concrete evidence exists. fileciteturn93file0

## Change

Added `.github/workflows/release-provenance.yml` with:

- `workflow_dispatch` for controlled manual qualification;
- `v*` tag pushes for release-shaped provenance;
- immutable SHA-pinned checkout, Python setup, artifact upload and attestation actions;
- pinned `build==1.3.0` and `cyclonedx-bom==7.3.1` tooling;
- sdist and wheel builds;
- SHA-256 release manifest;
- isolated target environment for SBOM generation;
- reproducible, validated CycloneDX JSON SBOM;
- release evidence artifact upload;
- signed provenance attestations for wheel and sdist;
- SBOM attestation for the wheel.

Verified upstream action refs before implementation:

- checkout `v7.0.1` → `3d3c42e5aac5ba805825da76410c181273ba90b1`; fileciteturn80file0
- setup-python `v7.0.0` → `5fda3b95a4ea91299a34e894583c3862153e4b97`; fileciteturn81file0
- upload-artifact `v7.0.1` → `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`; fileciteturn79file0
- attest `v4.2.2` → `1e69f48acb82d1966a394da916b4c1698aa569d6`. fileciteturn78file0

## Validation state

- Workflow implementation commit: `08086148aa813fa133ea41ace1bced2612f641e4`.
- Immutable attest pin correction commit: `5674db6e791b58fcc8a870c790a2df30c8810983`.
- The workflow intentionally does not run on ordinary `main` pushes. A real validation requires `workflow_dispatch` or a `v*` tag event.
- No successful provenance/SBOM execution is claimed yet.
- Existing V1 production blockers remain unchanged. Provenance does not substitute for audited AEAD, key custody, authenticated transport, authoritative trust/revocation, recovery qualification, or independent security review.

## Reusable learning

- [SECURITY] Artifact provenance proves lineage only when provenance and signer identity are verified; it does not certify artifact security. citeturn0search0turn0search2
- [SUPPLY-CHAIN] Release artifacts should be bound to exact digests and a trusted builder/provenance policy rather than mutable action tags.
- [PATTERN] Generate SBOM data from an isolated target environment so build/SBOM tooling does not appear as a false production dependency.
- [RULE] Do not mark release provenance complete until the workflow has actually executed and the resulting attestation/SBOM evidence has been observed and verified.
