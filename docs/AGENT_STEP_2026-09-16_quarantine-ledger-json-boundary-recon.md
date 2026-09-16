# Agent step: durable quarantine ledger JSON parsing boundary reconnaissance

Date: 2026-09-16
Agent: `gpt-5.6-luna`
Base commit: `d9001ef9e81a3e35e77d5a2a40d87075a3174d2e`

## Question

Can duplicate JSON object members in durable `QuarantineLedger` records be silently collapsed before the ledger's strict schema and type validation?

## Repository research

`QuarantineLedger.replay()` validates frame length, exact top-level fields, string/null scalar types, and non-negative timestamps, but it previously called default `json.loads`. Python's JSON decoder therefore discarded earlier values when an object contained the same member name more than once. The later schema checks could not recover the discarded member or prove that the persisted representation was unambiguous.

The ledger is append-only recovery evidence. Its replay path must fail closed on malformed records and must not reinterpret ambiguous persisted evidence as authoritative evidence.

## External research

- RFC 8259 section 4 states that duplicate object member names lead to unpredictable behavior because implementations differ in whether they report, preserve, or discard duplicates.
- OWASP secure coding/input-validation guidance recommends rejecting duplicate JSON keys at parsing boundaries instead of allowing parser-specific collapse.
- SQLite's durability documentation treats durable journal state as part of crash recovery and transaction correctness; malformed durable records therefore need explicit rejection rather than silent reinterpretation.
- External security/input-validation Agent Skills were inspected as advisory guidance. They reinforce validation at trust boundaries and fail-closed handling, but do not override FS project rules.

## Decision

Reuse the existing `_reject_duplicate_object_keys` parser helper and pass it as `object_pairs_hook` to `json.loads` in `QuarantineLedger.replay()`.

Add isolated regressions for duplicate top-level and duplicate string fields. Preserve the existing public `ValueError("quarantine ledger corruption")` contract and all existing schema/type checks.

## What remains unproven

This step does not claim physical media durability, crash atomicity beyond the ledger's existing length-prefixed/fsync behavior, or stronger recovery guarantees for concurrent writers. It only closes the parser ambiguity boundary.
