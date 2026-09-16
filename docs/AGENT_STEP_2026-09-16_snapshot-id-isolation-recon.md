# Agent step — snapshot ID isolation boundary

Date: 2026-09-16
Repository: `JoTalbot/fs`

## Finding

`SnapshotStore.get(snapshot_id)` previously interpolated the caller-supplied `snapshot_id` directly into `self.root / snapshot_id` before validating its shape. Because `pathlib.Path` treats absolute paths as absolute and accepts parent-directory components, a malformed or hostile identifier could address a filesystem path outside the managed snapshot root.

This was a repository-level isolation defect. The operation is a read, not a write, but the FS contract explicitly requires managed workspace boundaries and must not silently access arbitrary host state.

## Evidence

`SnapshotStore` already defines snapshot IDs as content-derived SHA-256 identities. Existing serialization checks verified the identity after reading the selected file, but that was too late to constrain which file was selected.

The regression suite already covered canonical object IDs and cross-snapshot substitution. It did not cover path traversal or absolute-path selection at the `SnapshotStore.get()` boundary.

## Remediation

`SnapshotStore.get()` now validates the snapshot identifier against the canonical lowercase 64-hex SHA-256 form before constructing the filesystem path. Invalid identifiers fail closed with `ValueError("invalid snapshot id")`.

A regression test covers parent traversal, nested traversal, an absolute POSIX path, and a Windows-style absolute path token. The test also proves that an outside file remains untouched and inaccessible through the API.

## Security boundary

This validation is an isolation/integrity guard, not an authority grant. A valid snapshot ID identifies a managed snapshot but does not grant filesystem authority, migration capability, recovery authority, or access to referenced host paths.

The fix follows the allowlist principle for structured identifiers and the requirement to validate input before file operations described by OWASP. See: https://owasp.org/www-community/attacks/Path_Traversal and https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html.

## Validation status

Implementation commit: `a8feab72fe1850446f251bad16a9f06a9e4f2fea`
Regression commit: `dc34832fa7899434f54b539e16fc877371b48b77`

GitHub Actions CI run `35101442752` / workflow run `691` was queued for the regression head at the time of this record. The regression is not treated as validated until the authoritative CI run completes successfully.

Production readiness remains unchanged: V1 still requires deployment-specific audited cryptography, secure key custody/lifecycle, authenticated/encrypted transport, authoritative trust/revocation, target-specific recovery evidence, independent security review, and release/supply-chain verification.
