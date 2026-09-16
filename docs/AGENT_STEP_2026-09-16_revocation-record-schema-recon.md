# Agent step: durable revocation record schema reconnaissance

Date: 2026-09-16
Agent: `gpt-5.6-luna`
Base: `f22ed8eba1cde27db72795379899be250ea5ef98`

## Question

Does the authoritative durable transfer-authority revocation registry fail closed on malformed persisted JSON field types, or does replay coerce non-canonical types into accepted values?

## Repository evidence

- `src/fs_overlay/authority_revocation.py` verifies event digests, sequence continuity, hash-chain continuity, duplicate authority IDs, and concurrent access under the file coordinator.
- `RevocationRecord.from_line()` currently constructs records with `int(data["sequence"])` and `str(...)` for `authority_id`, `reason`, `previous_digest`, and `event_digest` before validating the resulting record.
- Therefore JSON values such as numeric `authority_id` or boolean `sequence` can be coerced into strings/integers and potentially become authoritative replay state if the corresponding digest is constructed over the coerced representation.
- Existing tests cover durable reopen, duplicate revocation, event tampering, hash-chain breaks, sequence discontinuity, and concurrent writers, but not strict persisted-field types.

## External research

- NIST SP 1800-11, *Data Integrity: Recovering from Ransomware and Other Destructive Events*, emphasizes confidence in the accuracy and integrity of recovered data and auditing/reporting during recovery.
- NIST SP 1339 (June 2026) emphasizes creating, testing, and reviewing backups during recovery exercises.
- Public disaster-recovery agent-skill guidance reviewed at `arjunprabhulal/agent-skills` treats recovery evidence as something to verify rather than assume.
- GitHub's current Agent Skills documentation confirms shared skills are reusable workflows; external skills remain subordinate to repository security rules.

## Decision

Treat persisted revocation records as a strict schema boundary. Existing canonical records must continue to parse unchanged, while non-canonical JSON types must fail closed before coercion. The smallest implementation is explicit type checks for the persisted scalar fields, followed by existing semantic and digest validation. No new trust service, signature scheme, or deployment-specific provider is introduced.

## Why this fits FS

The revocation registry is an authoritative durable decision source. Accepting schema-coerced records weakens the distinction between valid durable state and malformed input. Strict replay preserves fail-closed authority semantics and makes malformed durable state unrecoverable by accidental coercion.

## What remains unproven

- The registry is not an authenticated trust-root or externally authoritative revocation service.
- The log has integrity chaining but no independent authenticity signature.
- Deployment durability and crash-recovery behavior remain target-specific qualification work.
- Atomic binding between a revocation check and a future host mutation executor remains outside this contract-only module.
