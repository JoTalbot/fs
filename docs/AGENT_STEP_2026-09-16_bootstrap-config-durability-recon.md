# Bootstrap Config Durability Recon

## Question
Can `MinimalBootstrap.initialize()` report a successfully persisted bootstrap configuration while a crash/power loss can still lose the newly created directory entry?

## Repository research
- `src/fs_overlay/federation_control.py` was reread at blob `127587e61a001a2b2188c8f065862b90f213209e` before modification.
- `MinimalBootstrap.initialize()` writes a temporary file, flushes and `fsync()`s that file, then replaces `config_path` with `os.replace()`.
- The containing directory is not synchronized after the replacement.
- `BootstrapConfig` is the durable node/root initialization record and `load()` is the restart path. Existing tests establish atomic replacement and strict schema validation, but not persistence of the directory entry across crash/power loss.
- `tests/test_federation_control.py` was reread at blob `29bdc9b00e851c8987f5a4f1d3650310ef2b302e` before modification.

## External research
- SQLite atomic-commit documentation explains that newly created durable journal entries require directory synchronization so the directory entry survives power loss. citeturn0search0turn0search1
- Linux `fsync(2)` states that `fsync()` flushes file data and metadata but does not necessarily ensure the containing directory entry has reached persistent storage. citeturn0search3
- External durability skill guidance identifies missing directory fsync after durable file creation/rename as a common crash-consistency failure mode. It was inspected as advisory only and does not override FS policy.

## Decision
Add a parent-directory durability barrier immediately after bootstrap config replacement. Reuse a small platform-aware helper local to this module: on non-Windows platforms open the containing directory with `O_DIRECTORY` when available and `fsync()` it; on Windows treat the operation as unsupported/no-op, matching the existing storage durability policy rather than inventing an unqualified Windows directory-fsync contract.

## Consequence
The existing atomic temp-file publication remains unchanged, while the POSIX persistence contract now includes the directory entry created/replaced by `os.replace()`. A regression test will verify that the directory-sync barrier is invoked after bootstrap initialization.

## Remaining uncertainty
This is crash-consistency evidence at the API-call boundary, not a proof that arbitrary hardware or filesystem implementations honor `fsync()` correctly. Target-specific power-loss testing remains part of production qualification.
