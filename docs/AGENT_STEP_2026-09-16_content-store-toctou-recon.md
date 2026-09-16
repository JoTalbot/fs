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
- Python documents directory-descriptor-relative filesystem operations and `follow_symlinks=False` where supported, which provides the building blocks for descriptor-scoped operations on POSIX systems. citeturn0search13turn0search17
- Microsoft documents reparse-point handling and `FILE_FLAG_OPEN_REPARSE_POINT`, but this does not by itself establish a portable Python equivalent for the complete multi-component write sequence. citeturn0search1turn0search5
- Current external agent/filesystem security material treats symlink substitution and path-based write-back as a TOCTOU/arbitrary-overwrite class of boundary issue. citeturn1search1turn1search3

## Skill discovery

The repository-local `fs-agent-core` skill was reread. External filesystem/agent-security material was inspected as advisory only; no external skill was adopted as authoritative. The external material reinforces the need to distinguish canonical-path checks from race-resistant filesystem operations.

## Decision

Do not immediately duplicate the carrier implementation inside `ContentAddressedStore`. First define whether the content-store root is an isolation/security boundary under the FS contract, or whether it is trusted deployment-owned storage where concurrent hostile mutation is explicitly out of scope.

If hostile concurrent mutation of managed storage is in scope, the write path needs a descriptor-scoped, no-follow primitive analogous to the carrier boundary, with explicit platform capability checks and fail-closed behavior. The implementation should cover both object shards and the manifest directory, and must preserve atomic publication plus existing fsync semantics.

If that threat is out of scope for this primitive, document the trust assumption rather than claiming race-resistant storage isolation.

## What remains unproven

- Whether `ContentAddressedStore` is required to resist hostile concurrent mutation of its root by the public architecture contract.
- Whether all declared Python/OS targets can support the required descriptor/reparse-point semantics.
- Whether a shared internal safe-directory primitive should be extracted without weakening the already-closed carrier boundary.
- A deterministic CI regression for concurrent shard-directory replacement is not yet implemented.

## Validation boundary

No runtime implementation was changed in this step. The finding is based on current repository source/tests, the already-closed carrier boundary, and current platform/security documentation. No stronger content-store isolation guarantee is claimed.

## Next safe step

Resolve the content-store trust-boundary contract from the current storage architecture/docs before implementing any write-path hardening. Avoid duplicating platform-specific filesystem primitives unless the contract requires the stronger guarantee.
