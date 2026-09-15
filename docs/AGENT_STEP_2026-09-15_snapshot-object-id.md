# Agent Step: Snapshot Object-ID Boundary

Date: 2026-09-15
Area: content-addressed workspace snapshot integrity

## Goal

Harden the snapshot boundary so persisted snapshot membership can only contain canonical content-addressed object IDs, without conflating object availability with authorization or recovery authority.

## Finding

`SnapshotStore` already binds a snapshot to its requested snapshot ID and verifies its Merkle root. Its `create()` path, however, previously accepted arbitrary strings as object references. That allowed structurally valid snapshot records to contain values that could never be valid content-addressed object IDs.

This is an integrity/schema boundary, not an availability guarantee. A valid 64-character SHA-256 object ID may legitimately be unavailable at snapshot creation time; availability remains a separate execution/recovery concern.

## Changes

- Added strict canonical lowercase SHA-256 object-ID validation to `SnapshotStore.create()`.
- Added the same validation to `Snapshot.from_bytes()` so persisted/tampered records fail closed before identity or Merkle acceptance.
- Added regression coverage for empty, short, long, uppercase, non-hexadecimal, and non-string object IDs.
- Added persisted-record tampering coverage for a noncanonical object ID.
- Preserved existing cross-object manifest and snapshot substitution regressions.

## Security boundary

- Object identity is validated independently from object presence.
- Object presence is not treated as authority.
- Snapshot creation still does not mutate host filesystem state.
- No materializer, recovery, transfer authority, or policy gate was weakened.
- FreeBSD native CI remains disabled and outside the release gate.

## Validation

Implementation commit: `9ff8ca589e792ed53b3ba8e0ecd0195735e29392`
Test commit: `42009a68fc8c3c8023830f49f21356e3800dd650`

Full CI validation is required for the new head before treating this step as qualified.

## Reusable learning

A content-addressed snapshot must reject malformed member identities at both construction and read boundaries. Do not add an object-existence requirement here: that would turn a logical immutable state catalog into a storage-availability gate and would blur integrity, availability, and authorization semantics.
