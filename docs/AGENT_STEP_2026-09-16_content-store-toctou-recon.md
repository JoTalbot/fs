# Agent Step 2026-09-16: Content Store Root TOCTOU Recon

## Question

Does `ContentAddressedStore` preserve the managed storage-root boundary if an attacker can replace the configured `objects` or `manifests` directories between path validation and filesystem mutation?

## Repository research

Current `ContentAddressedStore` validates object IDs before deriving paths, separates read-only `_validated_path()` from the write-only `_path()` directory-creation path, and verifies object/manifest content after reads. The carrier boundary was recently hardened with stable POSIX directory descriptors and no-follow traversal.

The content store itself still performs writes through pathname-based operations: `_path()` creates the shard directory by name, `tempfile.mkstemp(..., dir=target.parent)` opens a path-derived directory, and `os.replace()` operates on the pathname of that directory. `put_manifest()` similarly uses a path-derived temporary file and destination under `self.manifests`. These operations are safe against ordinary object-ID traversal, but the storage-root descendants are not held by stable descriptors during the whole write sequence.

A concurrent replacement of `objects/<shard>` or `manifests` with a symlink/reparse point could therefore redirect the temporary-file creation or later rename outside the configured storage tree if the deployment permits an untrusted concurrent filesystem actor.

This is distinct from the already-closed carrier boundary: `ContentAddressedStore` is a storage-engine primitive, not the carrier API, and its exact isolation guarantee is not currently stated with the same explicit hostile-concurrency contract.

## External research

- Linux `openat2(2)` documents `RESOLVE_BENEATH` and `RESOLVE_NO_SYMLINKS` as kernel-enforced path-resolution controls for untrusted paths and explicitly distinguishes them from final-component-only `O_NOFOLLOW`. citeturn0search0turn0search2
- Python documents directory-descriptor-relative filesystem operations and `follow_symlinks=False` where supported, which provides the building blocks for descriptor-scoped operations on POSIX systems. citeturn0search3turn0search6
- Current external agent/filesystem security material treats symlink substitution and path-based write-back as a TOCTOU/arbitrary-overwrite class of boundary issue. citeturn1search0turn1search8

## Skill discovery

The repository-local `fs-agent-core` skill was reread. External filesystem/agent-security material was inspected as advisory only; no external skill was adopted as authoritative. The external material reinforces the need to distinguish canonical-path checks from race-resistant filesystem operations.

## Contract resolution

The current architecture treats `ContentAddressedStore` as the local storage-engine spine, while the explicit isolation boundary is the carrier abstraction. `STORAGE_RESILIENCE.md` defines the store in terms of immutable content publication, durable journal visibility, snapshots, placement and quarantine; it does not define the caller-selected storage root as a hostile-concurrency isolation boundary. The CLI exposes the storage root as an explicit local filesystem location for audit/recovery/snapshot operations rather than as a capability-bearing carrier.

Therefore the observed pathname TOCTOU is a real limitation of the storage primitive, but not a demonstrated violation of its current security contract. The carrier boundary must continue to provide the stronger hostile-concurrency isolation guarantee where isolation is required. The content store must not silently claim equivalent protection.

## Decision

Do not duplicate the carrier implementation inside `ContentAddressedStore`. Document the content-store trust assumption explicitly and keep platform-specific descriptor/reparse-point hardening at the carrier boundary unless the architecture later promotes the content-store root to an independent isolation boundary.

If that contract changes, the write path needs a descriptor-scoped, no-follow primitive analogous to the carrier boundary, with explicit platform capability checks and fail-closed behavior. The implementation would need to cover both object shards and the manifest directory while preserving atomic publication and existing fsync semantics.

## What remains unproven

- The content store is not independently qualified as a hostile-concurrency isolation primitive.
- A future architecture could promote its root to an isolation boundary, which would require a new explicit contract and platform capability design.
- A deterministic CI regression for concurrent shard-directory replacement is intentionally not added because the current contract does not claim that guarantee.

## Validation boundary

No runtime implementation was changed in this step. The decision is based on current repository source/tests and architecture documentation plus current platform/security documentation. No stronger content-store isolation guarantee is claimed.

## Next safe step

Treat the content-store TOCTOU finding as a documented trust-boundary limitation and continue with a fresh reconnaissance of the next non-overlapping concrete fail-closed contract gap.
