# FS Overlay Storage Architecture

## 1. Core model

FS treats an existing file as a **carrier** and appends a self-describing FSOV block only when the carrier profile explicitly permits it. The original byte stream is immutable from FS's point of view and must remain readable by its native consumer.

A virtual container is split into logical chunks, encrypted/authenticated, then protected with erasure coding. Shards are distributed across independent approved carriers.

## 2. Safety invariants

1. No implicit whole-machine scan. The operator supplies one or more roots.
2. Never traverse protected/system paths.
3. Never modify a carrier without an explicit write policy and a successful format-safety check.
4. Never overwrite the original bytes.
5. Never rely on one metadata file for recovery.
6. Every shard has a cryptographic integrity check.
7. Every mutation is journaled.
8. Lost carriers trigger degraded-state detection, not silent data loss.
9. Repair may only use approved roots and carrier profiles.
10. A carrier is quarantined after unexpected external modification.

## 3. Pipeline

```text
Input
  -> optional compression
  -> AEAD encryption
  -> chunking
  -> erasure coding
  -> placement
  -> carrier append
  -> verification
```

Recovery is the reverse operation. It requires enough valid shards to satisfy the configured data-shard threshold.

## 4. Placement

Each carrier receives a score based on capacity, stability, supported profile, mutation frequency, and failure-domain diversity. The placement engine must avoid putting all shards in the same directory, filesystem, or other configured failure domain.

The 30% overhead is a **maximum**, not a target:

`overlay_bytes <= floor(original_size * max_overhead_ratio)`

For very small or unstable files, the effective limit is zero.

## 5. Metadata

Metadata is split into manifests and small recovery records. The manifest describes container ID, generation, shard geometry, carrier IDs, hashes, and format versions. Recovery metadata is itself replicated/erasure-coded so the loss of one index file does not destroy the container.

## 6. Self-healing

The auditor periodically checks carrier existence, length, FSOV header, checksum, and generation. When redundancy falls below policy, repair reconstructs missing shards from healthy shards and writes replacement shards to new approved carriers.

External changes to a carrier are never silently overwritten. The carrier is marked suspect and a repair plan is generated.

## 7. Encryption

Plaintext must not be sharded directly. Encryption occurs before erasure coding. The reference design expects an authenticated encryption construction such as AES-256-GCM or ChaCha20-Poly1305, with unique nonces and explicit key-version metadata.

Keys are supplied by an external key provider or operator-managed secret store. Keys are never embedded in carriers.

## 8. Concurrency

Carrier mutations use an advisory lock plus optimistic verification:

1. stat/hash carrier
2. acquire lock
3. re-check identity/hash
4. append
5. fsync
6. re-read/verify
7. release lock

If the file changed between steps 1 and 3, the operation aborts.

## 9. Recovery states

`HEALTHY -> DEGRADED -> REPAIRING -> HEALTHY`

If fewer than the required number of valid shards remain, the state becomes `UNRECOVERABLE` and FS must not claim successful recovery.
