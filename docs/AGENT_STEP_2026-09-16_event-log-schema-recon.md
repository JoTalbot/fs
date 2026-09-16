# EventLog durable schema reconnaissance, 2026-09-16

## Question
Can malformed persisted EventLog payloads be coerced or accepted without complete integrity validation during replay?

## Repository evidence
- `src/fs_overlay/event_log.py` persisted events with eight fields but replay previously validated the event hash only when `event_hash` was truthy.
- Replay coerced persisted `sequence` with `int(...)` and `event_hash` with `str(...)`; `reload()` repeated coercive reconstruction.
- Existing tests covered payload tampering, sequence gaps, concurrency, and append failure, but not malformed scalar types, missing integrity fields, or unexpected event fields.
- `AppendJournal` already enforces its own outer record schema, version, operation, and payload-dict type. The EventLog layer therefore owns the event-specific schema and hash-chain semantics.

## External evidence
- OWASP Input Validation recommends early syntactic and semantic validation, strong types/ranges, and rejection of malformed data before downstream processing.
- OWASP Logging requires event field names/types to be defined and validated, protects log integrity, and treats event data from other trust zones as untrusted.
- RFC 8259 notes that duplicate JSON member names have unpredictable receiver behavior. The current EventLog input is already materialized by `AppendJournal`, so this step does not invent a second raw-JSON parser; duplicate-member detection remains an outer journal-parser concern.

## Decision
- Require the exact eight fields emitted by EventLog.
- Require exact string/null/int/dict types without persisted-field coercion; reject bool-as-int and negative timestamps/sequence values.
- Require a present, canonical lowercase SHA-256 `event_hash`; validate optional `causal_parent` as null or the same SHA-256 form.
- Always recompute and compare the event hash, then enforce contiguous sequence and causal-parent linkage.
- Preserve existing event authority semantics. EventLog remains evidence/audit data and does not mint authority.

## Consequence
Malformed durable event records now fail closed before they can reconstruct sequence/hash state or be yielded to consumers. No new authority protocol or storage semantics were introduced.

## Validation boundary
GitHub Actions is authoritative. No local test runner is available.
