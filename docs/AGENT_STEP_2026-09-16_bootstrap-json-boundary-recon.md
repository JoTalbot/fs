# Agent step: bootstrap JSON parsing boundary

Date: 2026-09-16
Agent: gpt-5.6-luna
Area: `MinimalBootstrap.load()` durable bootstrap configuration parsing

## Question
Can duplicate JSON object members in the durable bootstrap configuration be silently collapsed before the existing strict schema/type validation?

## Repository research
- `src/fs_overlay/federation_control.py` was reread at the current `main` blob before modification.
- `MinimalBootstrap.load()` already enforces the exact field set, strict string/integer semantics, and semantic ranges, but it calls default `json.loads()`.
- Python's default JSON object parsing materializes duplicate names as one dictionary entry, so downstream exact-field/type checks cannot recover the discarded member.
- Existing bootstrap tests cover coercible types, unexpected/missing fields, semantic values, atomic replacement, and directory durability, but not duplicate object members.

## Internet research
- RFC 8259 §4 says JSON member names should be unique and warns that duplicate names make receiver behavior unpredictable; implementations may retain only one duplicate or reject the object. citeturn2search0
- OWASP Input Validation requires early syntactic and semantic validation of untrusted structured data and rejection of malformed input. citeturn0search0turn0search2
- External skill discovery found `secure-software-engineering` and `security-review`; both were inspected as advisory guidance. They reinforce strict serialized-data validation and trust-boundary review. citeturn1search0turn1search1

## Decision
Reject duplicate JSON object members at the bootstrap parser boundary with the same fail-closed `ValueError("malformed bootstrap config")` contract. Reuse a local duplicate-key hook rather than changing authority, bootstrap path semantics, or the existing schema contract.

## Consequence
A duplicate-key bootstrap record is rejected before schema/semantic interpretation. Existing valid configurations remain unchanged. Add regression coverage for a top-level duplicate field and a nested duplicate value container to prove parser rejection occurs before normal field validation.

## Validation
GitHub Actions is authoritative; no local test runner is available. Full 18-job CI validation is required after implementation.
