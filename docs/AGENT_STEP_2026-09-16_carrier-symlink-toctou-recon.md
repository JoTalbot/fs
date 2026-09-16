# Agent Step 2026-09-16: LocalDirectoryCarrier Symlink/TOCTOU Recon

## Question

Does `LocalDirectoryCarrier` preserve its configured-root isolation guarantee if another actor can mutate carrier descendants between containment validation and the filesystem operation?

## Repository research

Current `src/fs_overlay/carrier.py` at `0e88151ebe9160c833ac5b1fa19ccc9b733bc6c9` uses `Path.resolve()` in `_resolve()` and checks that the resolved candidate remains below the resolved carrier root. `put`, `get`, `delete`, and `contains` then perform ordinary pathname-based operations on the returned path.

The existing carrier tests cover durable directory fsync failure propagation and do not establish race-free symlink/reparse-point resistance.

The carrier contract describes the root as an explicit storage boundary. That makes pathname substitution relevant to the isolation contract rather than merely an availability concern.

## External research

- Linux `open(2)` documents the pathname-prefix TOCTOU problem and explains that directory-file-descriptor-relative APIs such as `openat()` avoid races caused by path components changing between validation and use. It also documents that `O_NOFOLLOW` applies to the final component and does not by itself protect earlier components. citeturn0search0turn0search2
- Linux `openat2(2)` provides kernel-enforced resolution controls including `RESOLVE_NO_SYMLINKS`, which covers symbolic links in path components rather than only the final component. citeturn0search12
- Python documents `os.open`, `os.mkdir`, and `os.replace` support for directory-file-descriptor-relative operations on supported platforms. citeturn1search2
- Windows `CreateFile` exposes `FILE_FLAG_OPEN_REPARSE_POINT`, which opens a reparse point itself instead of following it, while Microsoft documents that symbolic links, junctions, mount points, and other filesystem features are represented through reparse points. This is useful evidence for a Windows-specific no-follow primitive, but it does not by itself provide a portable Python-level beneath/openat2 equivalent for every path component. citeturn3search0turn3search2turn3search6
- Current agent/filesystem security work treats symlink substitution under a configured workspace as a concrete security boundary issue, and mature filesystem-jail designs distinguish ordinary canonical-path checks from kernel-enforced TOCTOU-safe opens. citeturn2search1turn2search4

## Skill discovery

The repository-local `.agents/skills/fs-agent-core/SKILL.md` was reread. External filesystem/agent-security material was inspected as advisory research only. No external skill was adopted as authoritative.

## Finding

`Path.resolve()` containment is useful against ordinary traversal and pre-existing symlink escapes, but it is not a proof that the subsequent pathname operation remains inside the root when an attacker can concurrently replace an intermediate component. The check and the use are separate filesystem operations.

Example threat shape:

1. `_resolve("sub/file")` resolves `root/sub/file` and confirms it is inside `root`.
2. Another actor replaces `root/sub` with a symlink to an external directory.
3. `get`, `put`, `delete`, or `contains` follows the changed path and may operate outside the configured root.

The same class of issue applies to parent-directory replacement during `put`, where `target.parent.mkdir()` and later temporary-file/rename operations use pathnames rather than a stable directory descriptor.

## Decision

Treat this as a real fail-closed isolation gap, but do not patch it with another `resolve()`/`commonpath()` check. That would leave the same TOCTOU window while creating the appearance of stronger security.

The next implementation step must first establish the supported platform contract:

- POSIX path operations should use stable directory descriptors and no-follow component traversal where the Python/platform APIs expose it.
- Linux should evaluate `openat2`-style kernel resolution for the strongest containment primitive available on the reference platform.
- Windows needs a native reparse-point-aware operation path or an explicitly weaker contract. `FILE_FLAG_OPEN_REPARSE_POINT` proves that Windows can open a reparse point without following it, but further work is required to make the whole multi-component carrier operation race-resistant. If equivalent enforcement cannot be established portably, the API must fail closed or explicitly narrow its guarantee rather than silently claim parity.

No `carrier.py` implementation change is made in this reconnaissance step.

## What remains unproven

- Whether the repository's supported Python/platform matrix exposes sufficient dir-fd and no-follow primitives on every target.
- Whether Windows can provide a sufficiently strong component-by-component handle-based implementation without introducing an unsupported native dependency.
- Whether the carrier contract should require a race-resistant capability or permit a weaker reference adapter outside production isolation claims.
- A deterministic CI regression for an actual concurrent component swap is not yet implemented.

## Next safe step

Perform a platform-capability reconnaissance for the repository's declared Python/OS matrix and design a minimal carrier operation primitive around the strongest common fail-closed semantics. Do not modify the public carrier contract until that analysis is complete.
