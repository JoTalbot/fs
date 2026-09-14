# FS Agent Log

Append concise, durable work records here. This is not a raw chat transcript. Each entry should let another agent understand what happened, why, what evidence exists, and what knowledge should be reused.

## 2026-09-14 | current-agent | trust-filter-at-read-time
Base: cad8aae1644d5485d42ae0a002124b4f8f66205f
Area: federation trust boundary and deterministic reconciliation
Goal: Prevent revoked or expired nodes retained in the last-observation directory from remaining eligible for reconciliation.
Research:
- `FederationDirectory.observe()` already checked trust at admission time, but `available()` returned retained advertisements without rechecking current trust.
- `FederationReconciler.plan_repairs()` consumes `available()`, so a node revoked after observation could remain a replication source until a newer advertisement arrived.
Skill discovery:
- Repository `fs-agent-core` and existing federation invariants remained authoritative; no external skill was needed.
Changes:
- Changed `FederationDirectory.available()` to apply `TrustStore.admit()` at read time.
- Preserved deterministic node ordering and the existing optional `now_ns` semantics.
- Added regressions covering post-observation trust disablement, expiry at a precise timestamp, and reconciliation refusing a disabled source.
Validation:
- CI #396 (`34858177089`) on the preceding transaction commit-marker head `cad8aae1644d5485d42ae0a002124b4f8f66205f` passed **18/18 jobs**.
- Fresh CI for the trust-filter change is pending; no pass is claimed yet.
Result: implementation `e7d54da4587135510a79a54eccd15dfff59a0df8`; tests `bb0e8bd45c097b465eb018518406c5e60ba29300`; status sync `ef721b82f9d6e63de7519536fe52a6e292a6da9b`.
Learning:
- [SECURITY] Trust admission is time-sensitive authority. A cached observation must not outlive revocation or expiry merely because its signature remains valid.
- [RULE] Federation read paths must revalidate current trust before making an identity actionable; admission-time validation alone is insufficient for long-lived directory entries.
Next: Validate the fresh head across the full matrix, then continue deterministic node-loss/reconciliation and journal recovery qualification.
