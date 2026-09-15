# Recovery audit concurrency qualification

The recovery audit log is evidence-only. It does not grant transfer authority,
apply a filesystem transition, or prove host state.

`RecoveryAuditLog.append()` now serializes replay, sequence allocation, hash-chain
linkage, and the durable append with the same cross-process file lock. This
prevents two independent processes from selecting the same sequence or
`previous_digest` and then corrupting the audit chain.

A multiprocessing regression starts two independent writers concurrently and
requires both events to survive, with contiguous sequence numbers and a valid
hash-chain link. The reader path remains lock-free and fail-closed on malformed,
tampered, or incomplete records.

This is a coordination guarantee for the reference append-only log, not a
substitute for a transactional database or external durability coordinator in
a production deployment.

Host filesystem mutation remains disabled.
