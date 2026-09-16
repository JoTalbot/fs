# Manifest JSON Parsing Boundary Recon

## Question
Can duplicate JSON object members in persisted manifests be collapsed by parsing before strict manifest schema and identity validation?

## Sources
- Repository: `src/fs_overlay/storage_engine.py`, `tests/test_storage_integrity.py`, current `main` before implementation.
- RFC 8259 §4: JSON object names SHOULD be unique; duplicate-name behavior is unpredictable across implementations.
- RFC 8785: canonical JSON objects MUST NOT contain duplicate property names.
- OWASP Developer Guide: duplicate JSON keys may be processed differently by parsers and should produce fatal parse errors.
- Canonical `fs-agent-core`: persisted JSON boundaries reject duplicate members before schema/integrity validation.

## Repository finding
`Manifest.from_bytes()` already enforced exact fields, strict scalar types, canonical object/chunk identifiers, metadata value types, and manifest identity. It still used default `json.loads(data)`, which collapses duplicate top-level and nested metadata members before those checks. Because manifests are content-addressed and read through `ContentAddressedStore.get_manifest()`, this parser behavior sits directly on an integrity path.

## Decision
Reject duplicate JSON object member names during `Manifest.from_bytes()` parsing with an `object_pairs_hook`, before schema and identity validation. Preserve the existing `manifest JSON is invalid` boundary and all storage, content-addressing, and authority semantics.

## Regression evidence
Add persisted-read regressions for duplicate top-level and nested metadata members through `ContentAddressedStore.get_manifest()`.

## Validation note
The first validation run exposed a test-fixture construction error and also revealed that the source snapshot had been overwritten from stale repository context, removing existing transaction-recovery APIs. The source was restored from the pre-step committed version while retaining only the manifest parser hardening, and the duplicate-key fixture plus journal-path expectation were corrected before the next validation run.

GitHub Actions remains authoritative; no local test runner is available.
