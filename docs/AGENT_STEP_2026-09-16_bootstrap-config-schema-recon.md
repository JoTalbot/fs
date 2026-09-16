# Agent Step Recon: Bootstrap Config Schema Integrity

Date: 2026-09-16
Agent: gpt-5.6-luna
Repository: `JoTalbot/fs`

## Repository research

`src/fs_overlay/federation_control.py` defines the durable `BootstrapConfig` JSON written by `MinimalBootstrap.initialize()` and loaded by `MinimalBootstrap.load()`. The current loader parses JSON and then coerces persisted `node_id`, `root`, `protocol_version`, and `initialized_ns` with `str()`/`int()` without enforcing an exact field set or exact persisted scalar types before constructing the configuration object.

The configuration is used as the bootstrap boundary for the explicitly selected filesystem root. `tests/test_federation_control.py` currently covers atomic bootstrap/write-read behavior, but does not exercise malformed persisted configuration types or unexpected fields.

The bootstrap boundary is intentionally narrow: it creates only the explicitly selected root/config and does not perform peer discovery, network setup, or host-wide mutation. This step therefore targets persisted configuration parsing only, not broader bootstrap behavior.

## External research

OWASP input-validation guidance recommends validating untrusted structured input as early as possible, at both syntactic and semantic levels, using strong types and allowlisted structure, and rejecting unexpected content. This directly applies to a persisted JSON bootstrap record because malformed values can otherwise be coerced into a different authoritative configuration state.

Sources:
- OWASP Input Validation Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- OWASP REST Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- NIST SP 800-57 Part 1 Rev. 5: https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final

NIST key-management guidance treats trust anchors and key-management material as security-relevant. This step does not turn `BootstrapConfig` into an authority token; it only prevents malformed persisted bootstrap state from being silently normalized into a different configuration.

## Skill discovery

Canonical project skill `fs-agent-core` was already inspected during the active schema-hardening series. No additional skill with a materially better fit for this narrowly scoped parser-hardening step was identified.

## Decision record

Harden `MinimalBootstrap.load()` with exact top-level field validation and exact scalar-type validation. Reject bool-as-int for numeric fields, reject unexpected or missing fields, require non-empty `node_id` and `root`, require `protocol_version >= 1` and `initialized_ns >= 0`, and preserve the existing `BootstrapConfig` semantics for records produced by `initialize()`.

Add regression tests for string-to-int coercion, bool-as-int coercion, unexpected fields, and malformed/missing fields. Do not add speculative path canonicalization, filesystem authorization, cryptographic identity binding, or network behavior to this parser step.

## Expected validation

GitHub Actions is authoritative because no local test runner is available. The implementation must be validated by the configured CI matrix before the boundary is closed.
