# Agent Step 2026-09-16: Manifest Write Immutability Recon

## Question
Can `ContentAddressedStore.put_manifest()` report success while an existing manifest object at the claimed content address is corrupted or no longer matches the requested manifest?

## Repository research
- Current `src/fs_overlay/storage_engine.py` was re-read from `main` at blob `4805f3ffaea639482ca936a2fc7bcdb2332708f3` before any implementation change.
- `Manifest.identity()` hashes the unsigned manifest representation, while `Manifest.from_bytes()` performs strict schema, type, duplicate-key, and identity validation.
- `ContentAddressedStore.get_manifest()` validates the requested object ID and then validates the loaded manifest.
- `ContentAddressedStore.put()` verifies an existing content object before returning an already-present object ID.
- `ContentAddressedStore.put_manifest()` currently checks `manifest.identity()` before writing, but when the target path already exists it returns the requested object ID without reading or validating the existing durable bytes.
- Existing `tests/test_storage_integrity.py` was re-read at blob `c59b0ed3170b228255c06dcc81f3bd33bb464585`. It covers tampered-manifest rejection on read and repeated content-addressed object writes, but does not require `put_manifest()` itself to fail closed on an existing corrupted target.

## External research
- SQLite's atomic-commit documentation describes durable commit as dependent on complete, flushed journal/state evidence; recovery must not treat an incomplete durable representation as a committed state. citeturn0search0
- OWASP path traversal guidance recommends known-good filesystem targets and explicit path construction rather than trusting filesystem names supplied by callers. citeturn2search1
- The external `secure-software-engineering` skill emphasizes enforceable controls at the boundary and evidence-backed release claims; it is advisory and does not override the FS contract. citeturn1search0

## Decision
Harden `put_manifest()` so an already-existing manifest target is read and validated before returning success. Reuse `Manifest.from_bytes()` and require the loaded manifest object ID to equal the requested ID. Do not overwrite the existing object, and do not invent a new recovery or authority mechanism.

## Consequence
A pre-existing corrupted or malformed manifest at a content address becomes an explicit write-time failure rather than a successful no-op that leaves durable corruption in place. Valid repeated writes remain idempotent.

## What remains unproven
- This does not establish protection against a concurrent filesystem attacker replacing paths between validation and use. Strong race-resistant host execution requires platform-specific descriptor/openat semantics and is outside this small cross-platform change.
- Production durability still depends on the deployment filesystem's actual fsync/atomic-replace behavior.
