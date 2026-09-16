# Agent Step 2026-09-16: Snapshot write durability reconnaissance

## Question
Can `SnapshotStore._write()` report a successful durable snapshot publication after the directory-entry fsync fails on Unix-like platforms?

## Repository research
- Current `src/fs_overlay/storage_resilience.py` was re-read from `main` at blob `06ead59bd8eb2999e62bb8968c71793562e86a2b` before implementation.
- `SnapshotStore._write()` writes and fsyncs the temporary file, atomically replaces the target, then attempts to fsync the containing directory.
- The directory fsync is wrapped in `except OSError: pass`, so a failure to persist the directory entry is silently converted into a successful return from `_write()`.
- `Snapshot.from_bytes()` and `SnapshotStore.get()` already provide strict schema and content-addressed integrity validation, so this step is about durability evidence, not snapshot parsing.
- Current `tests/test_storage_resilience.py` covers round-trip persistence and schema/integrity rejection but does not require directory-fsync failure to remain visible to the caller.

## External research
- SQLite's atomic-commit documentation treats directory/journal durability as part of crash-consistent commit evidence and describes syncing the directory so newly created durable entries survive power loss. citeturn0search0
- Python documents `os.fsync()` as the primitive that forces file-descriptor writes to disk; `os.replace()` is atomic on POSIX, but atomicity alone does not establish durable directory metadata. citeturn2search3turn2search1
- NIST SP 1800-11 emphasizes preserving the accuracy and precision of recovered data after destructive or corrupting events. citeturn0search4
- External `secure-software-engineering` guidance requires enforceable controls and direct evidence for security-sensitive state. It is advisory and does not override FS semantics. citeturn1search0

## Decision
On Unix-like platforms, a directory fsync failure must propagate instead of being swallowed, because `_write()` otherwise reports a successful durable publication without evidence that the new directory entry survived the required persistence boundary. Preserve the existing Windows behavior where directory fsync is intentionally unsupported by skipping that step on `os.name == "nt"`.

Add a regression that injects an `OSError` into the directory-fsync phase on a POSIX test run and requires snapshot creation to fail closed. Do not change snapshot identity, parsing, or cross-platform semantics beyond making the existing durability boundary enforceable.

## What remains unproven
- CI failure injection proves error propagation, not power-loss durability on every target filesystem.
- Windows continues to rely on its existing file flush/replace semantics because the project intentionally has no portable directory-fsync contract there.
