# Agent Step 2026-09-16: Durable Journal Directory-Entry Durability Recon

## Question

Can a newly created durable `AppendJournal` file lose its directory entry after a crash even though each appended record is flushed and `fsync`ed, causing durable security/recovery evidence to disappear on restart?

## Repository evidence

`AppendJournal.append()` writes the framed record, flushes the file, and calls `os.fsync(handle.fileno())`, but does not persist the parent directory after a new journal file is created. The shared `_fsync_directory()` helper already exists and is used by content-addressed object and manifest publication. `EventLog` is built on `AppendJournal`, so the same durability boundary covers federation admission/event evidence and other durable journals using this primitive.

Existing tests cover replay integrity, crash/restart transaction recovery, concurrency, and append failures, but there is no direct contract test that `AppendJournal.append()` performs the directory-entry durability barrier.

## External research

- Python `os.replace()` documentation states rename is atomic on POSIX, but atomicity does not itself establish durable directory-entry persistence.
- SQLite atomic-commit/recovery guidance treats filesystem synchronization as part of durable commit evidence rather than assuming a successful write implies crash persistence.
- OWASP transaction/workflow guidance emphasizes preserving server-side transaction state and preventing recovery from silently accepting missing or altered state.

## Skill discovery

Canonical `.agents/skills/fs-agent-core/SKILL.md` was reread. Its existing durable-filesystem rule states that a filesystem API must not claim durable publication when the final directory-entry persistence barrier fails. External secure-software/security-review skills were inspected as advisory methodology and do not override the local contract.

## Decision

Reuse the existing `_fsync_directory()` primitive in `AppendJournal.append()` after the file append and file `fsync`. On platforms where the helper cannot provide a directory barrier, its failure remains visible rather than being converted into successful durable publication. Add a focused regression test proving the journal append invokes the parent-directory durability barrier.

Do not redesign the journal format or add platform-specific kernel APIs in this step. The existing storage abstraction already has the required durability primitive.

## Consequence

First creation of a durable journal receives the same file-plus-directory publication discipline already used by content-addressed storage. This reduces the risk that a crash can erase the directory entry for the only durable event/admission/recovery record while the caller believes the append succeeded.

## Remaining evidence gap

CI can verify that the new durability call and regression test behave across the configured platforms. CI cannot by itself prove physical power-loss persistence on every filesystem; that remains a deployment-specific recovery qualification requirement.
