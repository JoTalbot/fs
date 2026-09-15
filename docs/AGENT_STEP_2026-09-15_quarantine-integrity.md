# Agent step: quarantine ledger fail-closed integrity

Date: 2026-09-15
Repository: `JoTalbot/fs`
Branch: `main`

## Finding

`QuarantineLedger.replay()` previously skipped malformed frames and continued returning later evidence. For an append-only recovery/evidence ledger, silently discarding corruption can produce an incomplete evidence view while presenting the surviving records as authoritative.

## Change

Replay now fails closed with `ValueError("quarantine ledger corruption")` for truncated frames, invalid length framing, malformed JSON, missing required fields, and other record decoding/type failures. Existing valid records are still preserved and replayed unchanged when the ledger is intact.

This remains evidence-only. The change does not grant authority, inspect or mutate host storage, or alter the separation between availability, authorization, recovery, and audit.

## Regression coverage

Added tests for malformed JSON/records and truncated frames. The prior soft-failure behavior is intentionally replaced because corruption of durable recovery evidence must not be silently ignored.

## Validation

The previous CI run #652 (`34988832996`) exposed a test expectation mismatch in the snapshot tamper regression and was not a product failure. The expectation was corrected in `efef7e47074a0cad5ed6e2631ce0496688d11d60`. The quarantine hardening and regressions are committed in `d474f54972c519699d6565ea6a72372deedb63a9` and `bc7614d6998d1b65277b13942704dfd401dfbb16` respectively. GitHub Actions remains authoritative; the new head must pass the full matrix before further implementation.

FreeBSD remains intentionally disabled.
