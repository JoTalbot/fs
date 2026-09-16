# Agent step: quarantine ledger schema integrity reconnaissance

Date: 2026-09-16
Agent: gpt-5.6-luna
Base: `12338a4d30b76956c5d77662514a5809eb3b2689`

## Question
Can malformed persisted `QuarantineRecord` JSON be coerced into recovery evidence during `QuarantineLedger.replay()`?

## Repository research
- `src/fs_overlay/storage_resilience.py` was read from current `main`, blob `92ce4872e9dcda5ab70cb6060779c75898912fa3`.
- `tests/test_storage_resilience.py` was read from current `main`, blob `21fc73ff7c0f7b7e3827784e59b901331a5022ea`.
- `QuarantineLedger` writes length-framed canonical JSON and replays the ledger as durable suspect-carrier evidence.
- Replay currently constructs records with `str(raw["carrier_id"])`, `str(raw["reason"])`, `int(raw["timestamp_ns"])`, and `str(raw["record_id"])`, while `observed_hash` and `expected_hash` are passed through without type validation.
- Replay does not reject unexpected or missing top-level fields before record construction.
- Existing tests cover malformed JSON, frame length mismatch, truncation, and valid append-only replay, but not type coercion or unexpected persisted fields.

## External research
- OWASP Input Validation: validate untrusted structured data as early as possible, enforce syntactic and semantic correctness, use strong types/ranges, allowlist expected structure, and reject unexpected content.
- OWASP ASVS 5.0 V1.5 Safe Deserialization: stored/transmitted representations require safe input handling and consistent parser behavior.
- External security-review skill: inspect deserialization boundaries, parser edge cases, and trust transitions before data reaches privileged or security-sensitive sinks.

Sources:
- OWASP Input Validation Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- OWASP ASVS 5.0 V1.5 Safe Deserialization: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x10-V1-Encoding-and-Sanitization.md
- External security-review skill: https://github.com/jakesterns/agent-skills/blob/main/plugins/security-review/skills/security-review/SKILL.md

## Skill discovery
- Canonical repository skill `.agents/skills/fs-agent-core/SKILL.md` was inspected and remains authoritative.
- External security-review and secure-software-engineering skills were discovered. Their relevant guidance is limited to security review/input handling and does not grant implementation authority.
- No external skill overrides FS's fail-closed authority/evidence rules.

## Decision
Harden only the persisted quarantine-record parser. Require:
1. exact top-level field set;
2. `carrier_id`, `reason`, and `record_id` to be strings;
3. `observed_hash` and `expected_hash` to be either strings or `None`;
4. `timestamp_ns` to be an actual non-negative integer, rejecting bool-as-int;
5. no coercive `str()`/`int()` conversion of persisted fields.

Do not impose a new hash algorithm or identifier format because the existing quarantine API does not define those semantics. Preserve the length framing, append-only behavior, and recovery-evidence meaning.

## What remains unproven
- This change does not establish authenticity of the quarantine ledger or production host durability beyond the existing fsync behavior.
- It does not create authority; quarantine evidence remains evidence only.
- Full validation requires the repository's GitHub Actions matrix because no local runner is available.
