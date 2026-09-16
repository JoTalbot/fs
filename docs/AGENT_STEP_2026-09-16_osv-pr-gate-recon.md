# OSV PR vulnerability gate reconnaissance

Date: 2026-09-16

## Scope

Evaluate whether OSV-Scanner can provide a repository-supported pull-request vulnerability gate without enabling GitHub Dependency Graph or inventing a production dependency lockfile/toolchain.

## Repository evidence

- `pyproject.toml` declares no runtime dependencies.
- Optional test dependency is `pytest>=8`.
- Optional crypto dependency is `cryptography>=44`.
- No selected production lockfile was found.
- Existing CI is GitHub Actions and is the authoritative validation path.

## External evidence

The current Google OSV-Scanner PR reusable workflow runs the scanner on the target branch and feature branch, compares the results, and can fail when new vulnerabilities are introduced. Its current published workflow is pinned to immutable action SHAs and does not depend on GitHub Dependency Graph.

The upstream workflow also demonstrates an important fail-closed property: if either scan fails without producing its result file, the comparison job fails instead of treating the missing result as a clean scan.

## Decision

Do not add the upstream reusable workflow verbatim yet. FS has no runtime dependency lockfile and only development/optional dependencies. A recursive scanner over the repository could therefore produce evidence about source-adjacent dependency manifests, but it would not constitute production dependency provenance or complete deployment SBOM evidence.

A narrowly scoped PR gate is technically feasible, but implementation should explicitly define what dependency surface is scanned and should fail closed on scanner execution failure. The gate must remain separate from production release qualification.

## Next

Before implementation, inspect the repository's actual dependency-bearing files and existing CI permissions/workflow conventions, then add the smallest pinned OSV scan that is meaningful for the declared Python project. Validate it on a real pull request before treating it as a control.