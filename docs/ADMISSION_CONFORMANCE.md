# Federation admission conformance

## Purpose

This document defines the independent admission-conformance boundary for protocol-v1 federation messages.

The canonical wire vectors prove deterministic serialization. The admission vectors prove semantic fail-closed behavior at the receive gate. They deliberately remain separate because an invalid message does not need a meaningful canonical digest in order to be rejected.

## Required negative cases

The protocol-v1 admission contract requires rejection of these ten cases:

1. malformed envelope
2. unsupported protocol version
3. negative sequence
4. empty message ID
5. duplicate message ID
6. sender sequence rollback
7. stale timestamp
8. future timestamp outside accepted clock skew
9. missing signature
10. key-admission failure, including unknown/revoked key or fingerprint mismatch

The machine-readable contract is `conformance/v1/admission-negative-v1.json`.

## Independent validation

`tools/independent_admission_conformance.py` validates the vector structure and the exact required case/gate/reason mapping using only the Python standard library. It must not import `fs_overlay`.

CI runs this validator before the internal test suite on Ubuntu, Windows and macOS with Python 3.11, 3.12 and 3.13.

## Adapter boundary

The negative contract specifies the semantic result, not a particular cryptographic implementation. A production key store, verifier, admission service or transport adapter may use different algorithms and storage systems, but an admitted message must still satisfy the same protocol-level gates.

Production adapter tests must additionally verify their own authoritative behavior: key lifecycle, trust decisions, durable ordering, transaction/commit semantics, transport authentication and recovery from ambiguous outcomes. Reference HMAC and in-memory adapters are development fixtures only and are not production security implementations.

## Fail-closed rule

If a required admission fact cannot be established, the message is rejected or held outside the admitted state. Discovery never substitutes for trust, capability never substitutes for authority, and a timeout never becomes an implicit lease.
