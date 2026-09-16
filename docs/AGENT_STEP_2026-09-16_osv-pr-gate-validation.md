# OSV PR vulnerability gate validation

Date: 2026-09-16

## Scope

Validate that the pinned OSV-Scanner PR workflow triggers in a real pull-request context and record whether the scanner completes successfully.

## Current evidence

- Validation branch: `ci/osv-pr-gate-validation`
- Workflow implementation commit: `f373bf1a7d3480d4c3c635497c18f30b6b874c48`
- The workflow uses read-only `contents` permission and immutable action SHAs.
- No pull-request workflow run is currently visible for the implementation commit through the available GitHub Actions API.

## Status

No successful OSV scan is claimed. A workflow definition existing in the branch is not equivalent to execution evidence.

## Safety boundary

The proposed workflow is a CI vulnerability signal only. It does not establish production dependency provenance, a deployment lockfile, an SBOM, or production release qualification.
