# FS Storage Resilience

The reference storage layer is intentionally conservative: immutable data may be prepared ahead of a metadata commit, while visibility is controlled by a durable journal marker.

## Durability model

1. Chunk data is content-addressed and written through a temporary file.
2. The chunk is flushed and `fsync`-ed before publication.
3. The manifest is written immutably and flushed before publication.
4. A transaction writes `transaction_begin`, staged `commit` records, then `transaction_commit`.
5. Recovery publishes only staged commits belonging to a transaction with a durable commit marker.
6. An incomplete transaction is ignored rather than guessed into existence.

This is crash-consistent journal visibility. It is not a distributed transaction protocol.

## Snapshots

`SnapshotStore` records an immutable list of logical object IDs plus a deterministic Merkle root. Snapshot identity is derived from its canonical contents. A snapshot is therefore a versioned point-in-time catalog, not a second copy of the data.

## Recovery graph

`RecoveryGraph` provides deterministic topological ordering for recovery actions and rejects cycles or unknown dependencies. Recovery ordering must be explicit; wall-clock ordering is insufficient.

## Carrier placement

`PlacementPlanner` accepts only approved and healthy carriers with enough free capacity. Capacity, locality and failure-domain diversity are explicit inputs. A plan is not permission to mutate a carrier.

## Quarantine

`QuarantineLedger` records unexpected carrier changes without overwriting evidence. Suspect carriers are kept out of automatic placement until policy explicitly clears them.

## Recovery states

- `HEALTHY`: all configured shards are valid.
- `DEGRADED`: enough valid shards remain, but redundancy is below the configured target.
- `REPAIRING`: an approved repair operation is in progress.
- `UNRECOVERABLE`: fewer than the required data-shard threshold remains.

FS must never report successful recovery in `UNRECOVERABLE` state.

## Cryptography and erasure coding

The storage engine exposes explicit AEAD and erasure-coding provider contracts. The HMAC envelope is integrity-only and must not be used as encryption. No unaudited cryptographic or erasure implementation is silently promoted to a production guarantee.
