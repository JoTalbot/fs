# FS Federation Protocol Boundary

FS federation is deliberately split into protocol semantics and transport implementation.

## Envelope

Every federation message carries:

- sender node identity;
- unique message ID;
- monotonically increasing sender sequence;
- message type;
- issue timestamp;
- canonical payload;
- signature supplied by an audited cryptographic provider.

The canonical unsigned envelope is hashed with SHA-256 for stable content identity. The hash is not a signature and does not establish trust.

## Receive gate

```text
transport
   -> parse envelope
   -> verify signature
   -> verify freshness
   -> reject replay/reordering
   -> policy/trust evaluation
   -> protocol handler
```

No handler is invoked before these checks succeed.

## Replay protection

`ReplayGuard` tracks the highest accepted sequence per sender and previously accepted message IDs. Duplicate IDs, stale/future timestamps, and non-increasing sequences are rejected.

This is an in-memory reference primitive. A production receiver must persist or checkpoint replay state according to its durability requirements.

## Replication

`ReplicaAction` is an already-authorized action. `ReplicaExecutor` uses an injected adapter, hashes the source bytes before writing, performs the write, then reads the target back and verifies the same hash.

The executor does not:

- discover peers;
- establish trust;
- select arbitrary targets;
- choose a carrier root;
- open network connections;
- grant authority.

Those responsibilities remain outside the execution boundary.

## Self-healing

`SelfHealingPlanner` converts explicit observations into deterministic replica actions. It considers only trusted nodes, requires a healthy verified source, selects the source deterministically, and limits targets to healthy missing replicas. A plan is not execution. Invalid, missing, or untrusted observations cannot become a repair source.

## Regression coverage

Focused tests cover:

- signed envelope acceptance and duplicate replay rejection;
- sender sequence rollback rejection;
- stale and future timestamp rejection;
- invalid signature rejection;
- source integrity failure without a write;
- target corruption detected after copy;
- deterministic trusted-source and target selection;
- exclusion of unhealthy/untrusted repair participants;
- no repair when the desired replica count is already satisfied.

## Minimal initiator

A node may begin with only an explicitly selected FS root and local configuration. Federation participation requires explicit identity and trust admission. The smallest node therefore remains useful without requiring a central server.

## Production boundary

The reference implementation intentionally does not claim production cryptography, network security, durable distributed consensus, or distributed atomicity. Those require audited providers, transport security, persistent protocol state, and interoperability testing.
