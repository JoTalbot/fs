# Release provenance boundary reconnaissance

Date: 2026-09-16
Repository: `JoTalbot/fs`
Base: current `main` at step start

## Scope

Focused review of the release/supply-chain boundary: build workflow, production qualification record, reference deployment profile, signed-release roadmap items, and artifact provenance requirements. This step does not implement a release pipeline or claim production certification.

## Research

- GitHub artifact attestations documentation: attestations bind releasable artifacts to workflow/repository/commit/event provenance; meaningful security benefit requires verification and signer identity validation. Routine test builds are not the intended target.
- SLSA v1.2 provenance specification: provenance is verifiable information describing where, when, and how an artifact was produced; verification requires trust in the builder/provenance chain.
- Repository `AGENTS.md`: substantive steps require fresh repository research, external research, and skill discovery; evidence must distinguish planned, executed, observed and verified states.

## Repository evidence

- `.github/workflows/ci.yml` contains test and candidate crypto-provider jobs only. It does not define a release artifact publication or attestation workflow.
- `docs/PRODUCTION_SECURITY_QUALIFICATION.md` requires exact provider/version, dependency/supply-chain review and external security evidence.
- `docs/PRODUCTION_REFERENCE_PROFILE.md` requires exact FS artifact/commit, provider versions, dependency provenance, qualification commands and audit references, while explicitly keeping the production decision `BLOCKED` until concrete evidence exists.
- `docs/ROADMAP.md` still treats signed releases and supply-chain verification as Phase 11 work.

## Finding

No repository-level fail-open security defect was found in the release provenance boundary. Absence of release attestation is currently an unfinished production/release capability, not an unsafe runtime fallback. Adding attestations to the ordinary test matrix would conflate test evidence with releasable artifact provenance and would not by itself satisfy the production-security gate.

## Decision

- No runtime or CI code change in this step.
- Do not introduce a release-attestation workflow until the release artifact, publication target, trusted builder policy, and verification policy are concretely selected.
- Preserve the existing production blocker rather than treating provenance as a substitute for AEAD, key custody, transport authentication, trust/revocation, recovery, or independent security review.

## Reusable learning

- [SECURITY] Artifact provenance proves lineage only when the provenance and signer are actually verified; it does not certify the artifact's security.
- [RULE] Test CI and release provenance are separate evidence classes and must not be merged merely because both execute GitHub Actions.
- [SUPPLY-CHAIN] A production release gate should bind an exact artifact digest to an explicitly trusted builder/provenance policy and retain verification evidence outside secret material.

## Validation boundary

Source/document and external-standard reconnaissance only. No implementation was changed, so no new CI validation claim is made.
