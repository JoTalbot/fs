# Immutable State, Content Identity and Lineage

FS separates logical identity from content identity and physical location.

## Identity layers

```text
ObjectID   = what logical object this is
ContentID  = what content/state representation it contains
Location   = where a current physical representation resides
Generation = which committed version it represents
```

An object may move without changing ObjectID. A new content generation changes ContentID and Generation.

## Content addressing

Content-addressed storage enables deduplication, verification, efficient replication and copy-on-write snapshots. Identical immutable content can be shared by multiple logical objects when policy permits.

## Merkle DAG

The logical state can be represented as a Merkle DAG:

```text
Environment root
 ├─ Volume root
 │   ├─ Object root
 │   └─ Object root
 └─ Package root
```

Parents reference child content hashes. This supports efficient comparison, snapshotting, replication and integrity verification.

## Immutable objects

Events, snapshots, package manifests, committed content objects and audit records should be immutable. A modification creates a new generation rather than rewriting historical state.

## Lineage

A committed object can retain references to:

```text
parent generation
source package
creating actor
policy version
content hash
snapshot
related events
```

This creates a verifiable lineage from package to environment, volume, object, shard and carrier.

## Time travel and branches

Immutable state enables historical views and copy-on-write branches:

```text
snapshot S
   ├─ production
   ├─ test
   └─ experiment
```

Branches share immutable content until a change requires new content. Promotion and merge must be policy-controlled and conflict-aware.
