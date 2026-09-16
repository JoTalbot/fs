# Recovery audit schema integrity reconnaissance

Date: 2026-09-16

## Scope

Fresh reconnaissance of the durable `RecoveryAuditLog.replay()` parser in
`src/fs_overlay/workspace_transfer_recovery_audit.py` after the federation
envelope boundary was closed.

## Repository findings

`RecoveryAuditLog` is an append-only, hash-chained recovery evidence log. Its
records are not authority and do not apply filesystem transitions. The
existing implementation already serialized replay, sequence allocation,
hash-chain linkage, and append under a cross-process file lock.

The replay parser, however, reconstructed persisted records with coercive
`int(...)` and `str(...)` conversions. It also accepted unexpected persisted
fields and did not enforce exact scalar types before enum conversion and
hash-chain validation. This meant malformed durable data could be normalized
into apparently valid recovery evidence instead of being rejected at the
schema boundary.

Existing semantic protections were retained: materializing-phase binding,
SHA-256 digest validation, decision/transition consistency, contiguous
sequence validation, previous-digest linkage, and event-digest verification.

## External research

Fresh external research reviewed RFC 8259 JSON interoperability guidance and
OWASP guidance for REST input validation and safe deserialization. RFC 8259
notes that duplicate object member names can lead to unpredictable receiver
behavior. OWASP guidance calls for strict type/range/format validation and
rejection of unexpected content before trusted processing.

## Decision

Harden only the persisted recovery-audit wire/schema boundary:

1. Require the exact persisted field set.
2. Require version exactly `1` and exact integer typing, excluding booleans.
3. Require positive integer sequence values.
4. Require nonempty strings for persisted identifiers, enum tokens, reason,
   evidence digest, and event digest.
5. Allow `previous_digest` only as a nonempty string or `null`.
6. Reject duplicate JSON object member names during parsing.
7. Preserve all existing semantic, hash-chain, and digest checks after schema
   validation.
8. Do not turn audit evidence into authority and do not change recovery
   execution semantics.

## Evidence

Base implementation before change: `7717ea63e88486dff12a979d0eaae55c596076ff`.

Implementation: `86bc767e76b048bf31eb7f230afe3fb51bde91a5`.

Regression tests: `5a51e2c6900cf93e9fa0b08c892a513e97367e1b`.

CI validation is pending; GitHub Actions remains authoritative because no
local test runner is available.
