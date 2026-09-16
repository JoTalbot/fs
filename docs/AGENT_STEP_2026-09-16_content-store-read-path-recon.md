# Agent Step: Content-Store Read-Path Mutation Boundary

## Question

Does `ContentAddressedStore.get()` mutate managed filesystem state while resolving a valid object path, and does that violate the storage read-path contract?

## Repository research

`ContentAddressedStore._path()` validates a canonical 64-hex object ID, derives the two-character shard directory, and unconditionally calls `directory.mkdir(exist_ok=True)`. Both `put()` and `get()` call `_path()`. Therefore a read of a valid but absent object creates the shard directory before `read_bytes()` raises `FileNotFoundError`.

`put()` legitimately needs shard-directory creation before `mkstemp()` and publication. `get()` does not. Existing object integrity and path-validation tests do not establish that an absent-object read is side-effect free.

## External research

- Python `pathlib.Path.mkdir()` is explicitly a directory-creation operation, while `Path.read_bytes()` reads an existing file. Python documentation therefore supports separating path calculation from write-time directory creation.
- POSIX directory creation is a filesystem mutation; a read-only lookup should not need to create a directory.
- The project-local `fs-agent-core` rule prefers read-only inspection before mutation and distinguishes desired state from actual state.

## Decision

Split content-store path resolution into:

1. a pure validated path helper that performs no filesystem mutation; and
2. the existing write path, which creates the shard directory only for `put()`.

Change `get()` to use the pure helper. Preserve canonical object-ID validation, integrity verification, and existing write durability behavior.

## Consequence

A missing-object read remains a normal `FileNotFoundError` but no longer creates a shard directory. Writes retain their required directory creation. This closes a concrete read-path mutation boundary without adding new authority or storage semantics.

## Validation plan

Add a regression proving that `get()` of a valid absent object leaves the corresponding shard directory absent. Full GitHub Actions CI is the authoritative validation boundary because no local test runner is available.

## Unresolved

No claim is made about filesystem-level side effects outside the managed carrier root or about platform-specific metadata reads beyond the tested path-resolution behavior.
