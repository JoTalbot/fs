# Agent step: LocalDirectoryCarrier directory-durability boundary reconnaissance

Date: 2026-09-16
Agent: `gpt-5.6-luna`
Base commit: `b075a02980dcdcb0daa3c37ef1eb19a6be392efd`

## Question

Can `LocalDirectoryCarrier.put()` or `delete()` report successful durable mutation when the directory-entry synchronization required for crash durability fails?

## Repository research

`LocalDirectoryCarrier.put()` writes and fsyncs the temporary file, atomically replaces the target, then calls `_fsync_directory(target.parent)`. `delete()` unlinks the target and calls the same helper. Before this step `_fsync_directory()` caught every `OSError` and returned normally. Therefore both mutating APIs could return success after a failed directory fsync, despite the carrier being used as a storage boundary where callers can reasonably treat successful return as completed persistence.

The carrier's explicit root and path-containment checks are unchanged. No authority or path-scope semantics depend on swallowing directory-fsync errors.

## External research

- Linux `fsync(2)` documents that syncing a file does not necessarily sync the containing directory, so directory metadata needs its own synchronization when directory-entry durability matters. citeturn2search0
- POSIX `fsync()` specifies that synchronization completes or reports an error; suppressing the error removes evidence that the requested synchronization succeeded. citeturn2search3
- SQLite's atomic-commit documentation explicitly syncs directories on Unix when durable visibility of a newly created journal entry matters. citeturn2search1turn2search2
- External `secure-software-engineering` guidance requires enforceable controls and direct evidence for security-sensitive state. Durability-oriented skill guidance also treats missing directory synchronization as a distinct crash-safety failure mode. These sources are advisory and do not override FS portability constraints.

## Decision

On platforms where the carrier's directory-fsync implementation is supported, propagate `OSError` from `_fsync_directory()` instead of swallowing it. Preserve the explicit Windows boundary by returning without attempting a directory fsync when `os.name == "nt"`; FS does not invent an unverified Windows directory-durability primitive.

Add regressions proving that:

1. `put()` raises when the second fsync, the directory fsync, fails.
2. `delete()` raises when its directory fsync fails.

The tests intentionally verify failure propagation rather than claiming rollback of the already-visible namespace mutation. A failed durability barrier means the caller cannot be told that durable publication completed.

## What remains unproven

This change does not prove physical media durability on filesystems or storage devices that violate their platform contracts, nor does it define a stronger Windows durability guarantee. It only prevents FS from suppressing an observed directory-fsync error on supported platforms.
