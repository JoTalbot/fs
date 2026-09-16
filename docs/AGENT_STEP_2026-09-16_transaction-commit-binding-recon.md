# Agent step: transaction commit-marker binding reconnaissance

Date: 2026-09-16
Agent: `gpt-5.6-luna`
Base commit: `ea9c57e81eb8a112077dd04ea539309c0fb4399c`

## Question

Does `transaction_commit.object_ids` carry authoritative recovery state that must be matched to staged `commit` records, or is it redundant metadata whose mismatch cannot change recovered inventory state?

## Repository research

`Inventory.load()` validates `transaction_commit.object_ids` as a list of canonical object IDs, but does not use that list to create, delete, or select inventory records. Recovery publishes only the staged `commit` records accumulated while the transaction ID is pending. The normal writer constructs the terminal `object_ids` list from the same prepared manifests that it stages as `commit` records.

A malformed complete journal can therefore contain, for example, a staged object `A` followed by `transaction_commit.object_ids=[B]`, and replay will still publish `A`. Conversely, a marker naming `B` cannot cause `B` to be published when `B` was never staged. The marker cannot mint inventory authority by itself.

The preceding transaction-state hardening already rejects unknown terminal records, duplicate/reopened transaction IDs, and transaction-tagged commit records without a pending begin. The remaining `object_ids` field is therefore not a second recovery authority; it is redundant transaction evidence.

## External research

- SQLite documents that durable transaction state must identify the point at which changes become committed and that recovery must not treat incomplete journal state as committed state. Its WAL format uses a commit marker tied to the written frames, while rollback journals contain the information needed to restore the pre-transaction state. citeturn2search0turn1search2
- OWASP Transaction Authorization requires transaction data and state transitions to be validated server-side and protected from modification. OWASP Business Logic Security similarly recommends explicit server-side state machines and validation of meaningful field combinations. citeturn1search5turn1search0
- External `secure-software-engineering` guidance recommends explicit acceptance criteria, enforceable controls, and direct evidence for security-sensitive state. citeturn0search0

## Decision

Do **not** add an `object_ids` equality check in this step.

The mismatch is a durable consistency/audit-quality weakness, but it is not currently a fail-open recovery-authority defect: the disputed field cannot alter the recovered inventory set, while the staged commit records remain the actual source of publication. Adding a new equality invariant would be a defense-in-depth integrity assertion and would need an explicit contract for ordering, duplicate object IDs, and compatibility with historical journals before becoming a mandatory replay rule.

If a future audit establishes that `object_ids` is intended to be authoritative commit evidence rather than redundant metadata, promote it to a separate schema/semantic contract and require exact binding to the staged records before publication.

## Validation boundary

No runtime implementation was changed in this step. The conclusion is based on current source inspection, existing recovery tests, and external transaction/journal semantics. No additional security guarantee is claimed.

## Result

No code change required. The next safe area is a fresh, non-overlapping recovery or storage-integrity boundary rather than repeating transaction-state or JSON parser work.
