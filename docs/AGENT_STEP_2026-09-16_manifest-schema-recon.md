# Manifest schema reconnaissance

## Question
Can persisted `Manifest.from_bytes()` coerce malformed durable fields into authoritative manifest state, despite content-addressed identity checks?

## Repository evidence
- `Manifest.from_bytes()` currently checks only `format_version`, then constructs the dataclass using `str(raw["object_id"])`, `int(raw["size"])`, `tuple(raw["chunks"])`, and `int(raw["chunk_size"])`; `metadata` is accepted without type validation.
- `ContentAddressedStore.get_manifest()` validates the requested object ID before filesystem access and then checks that the loaded manifest object ID equals the requested ID. These controls do not make malformed persisted field types invalid before construction.
- `Manifest.unsigned()` and `identity()` operate on the constructed values, so coercion can change the representation being hashed.
- Current integrity tests cover tampered manifest bytes and object-ID mismatch, but do not cover wrong JSON types, unexpected fields, malformed chunk IDs, invalid metadata, or invalid numeric ranges.

## Internet evidence
- OWASP Input Validation recommends syntactic and semantic validation as early as possible and allowlisting expected structured input.
- OWASP ASVS 5.0 V2.2.1 requires positive validation against expected structures/ranges; the associated guidance treats strongly typed structured data and defined schemas as required validation for security-relevant input.
- These sources support rejecting malformed persisted structured data rather than coercing it into a different representation.

## Skill evidence
- External `secure-software-engineering` skill (`magnus919/agent-skills`) was inspected. It requires explicit security acceptance criteria, validation of untrusted structured data, evidence-backed review, and recording residual risks. It is methodology only and does not override `fs-agent-core`.

## Decision
Treat persisted manifests as untrusted durable input. Harden only `Manifest.from_bytes()` and its direct regression tests. Validate an exact top-level field set and exact field types before constructing `Manifest`; validate object/chunk IDs as lowercase SHA-256 strings, nonnegative size, positive chunk size, exact format version, and metadata as either null or a string-to-string mapping. Preserve the existing canonical identity calculation and valid empty-manifest behavior. Do not introduce a new schema dependency or broaden the change into unrelated storage/refactoring work.

## Consequence
Malformed complete manifest records fail closed before coercion. Valid manifests retain their existing serialized representation and identity semantics. This step does not establish physical chunk availability or production cryptographic qualification; those remain separate evidence boundaries.

## Unproven
CI validation is required after implementation. The change does not by itself prove filesystem durability, crash consistency, or production security qualification.
