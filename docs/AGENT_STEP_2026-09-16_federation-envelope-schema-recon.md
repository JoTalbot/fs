# Agent Step 2026-09-16: Federation Envelope Schema Recon

## Question
Does `FederationEnvelope.from_bytes()` safely reject malformed untrusted wire data before it reaches signature and replay admission?

## Repository research
- Re-read `AGENTS.md`, `AGENT_STATUS.md`, `src/fs_overlay/federation_protocol.py`, and `tests/test_federation_protocol.py` from `main`.
- `FederationReceiver.receive()` verifies the parsed envelope before replay admission, but parsing itself occurs before signature verification.
- `FederationEnvelope.from_bytes()` previously used `str()` and `int()` coercions, accepted missing/extra top-level fields through `get()`, and treated non-string/non-null signatures as absent.
- `ReplayGuard` already rejects empty sender/message IDs and negative sequence values, but that check happens after object construction.
- Existing payload semantics intentionally allow an arbitrary JSON object, so payload fields must not be narrowed by this step.

## External research
- RFC 8259: JSON object member names should be unique; duplicate names can produce unpredictable receiver behavior across implementations. Parsers may impose limits on size, depth, ranges, and string contents. 
- OWASP Deserialization guidance: untrusted deserialization requires strict type constraints and safe input handling; deserialized objects should be populated through validated data paths.
- OWASP REST/Input Validation guidance: validate untrusted objects for type, range, format, and unexpected content at the boundary.

## Skill discovery
- Canonical repository `.agents/skills/fs-agent-core/SKILL.md` was inspected and remains authoritative.
- Fresh external security-review skills were inspected. They emphasize tracing untrusted input to privileged behavior and reviewing deserialization/parser edge cases. They are advisory and cannot override FS's fail-closed contract.

## Decision
Harden only the wire-schema boundary. Require the exact top-level field set:
`sender_node`, `message_id`, `message_type`, `sequence`, `issued_ns`, `payload`, `signature`.

Require exact types without coercion:
- protocol identifiers: non-empty strings;
- sequence and issued timestamp: real non-negative integers, excluding bool;
- payload: dict;
- signature: string or null, with strict base64 decoding for strings.

Reject duplicate top-level JSON member names during parsing. Preserve arbitrary JSON values inside `payload` and preserve existing signature, freshness, replay, and receiver behavior. Do not introduce new identifier-format or authentication semantics.

## Security consequence
Malformed wire data cannot silently become a different valid envelope through Python scalar coercion or ambiguous duplicate top-level fields. Authentication and replay semantics remain unchanged.

## What remains unproven
- Full CI validation is required.
- This step does not establish transport encryption, authenticated transport provider qualification, or production security certification.
- JSON size/depth/resource limits remain a separate concern and are not invented here without an explicit project contract.
