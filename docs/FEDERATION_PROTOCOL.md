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

## Durable replay state

`DurableFederationState` persists accepted message IDs and sender sequence high-water marks through the existing append-only `EventLog`. On restart it reconstructs the admission state before accepting new envelopes.

The durable state object is intentionally **not** an authentication layer. Callers must first establish signature, trust and freshness. Production deployments additionally need journal compaction, concurrency coordination and a durable storage policy appropriate to their failure model.

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

## Placement policy

`ReplicaPolicy` selects only healthy candidates not already hosting the object. It prefers candidates in failure domains not represented by existing replicas, then deterministically fills remaining replica slots using capacity, locality and node ID. Placement remains a policy decision and never grants permission to mutate a carrier.

## Audit trail

`FederationAuditTrail` records reconciliation decisions and replica execution outcomes through `EventLog`. A result can reference the decision's event hash as `causal_parent`, creating a verifiable decision -> execution chain without coupling the audit layer to a particular transport.

## Self-healing

`SelfHealingPlanner` converts explicit observations into deterministic replica actions. It considers only trusted nodes, requires a healthy verified source, selects the source deterministically, and limits targets to healthy missing replicas. A plan is not execution. Invalid, missing, or untrusted observations cannot become a repair source.

## Adapter contracts

`federation_adapters.py` defines dependency-injection boundaries for:

- `FederationTransport`;
- `FederationSigner`;
- `KeyProvider`.

`production_adapters.py` adds explicit deployment boundaries for:

- `SecureKeyStore` for protected key-material storage;
- `AuthenticatedTransport` for authenticated/encrypted federation channels and peer identity;
- `NodeAdmission` for authoritative node admission and revocation.

These contracts deliberately do not select a network protocol, certificate authority, cryptographic library, HSM, operating-system keystore, or admission database. Implementations must supply those policies and security properties explicitly.

## Regression coverage

Focused tests cover:

- signed envelope acceptance and duplicate replay rejection;
- sender sequence rollback rejection;
- stale and future timestamp rejection;
- invalid signature rejection;
- durable replay state across restart;
- source integrity failure without a write;
- target corruption detected after copy;
- deterministic trusted-source and target selection;
- failure-domain-aware placement;
- exclusion of unhealthy/untrusted repair participants;
- audit decision/result causal linkage;
- adapter contract importability;
- production security adapter contract importability.

## Minimal initiator

A node may begin with only an explicitly selected FS root and local configuration. Federation participation requires explicit identity and trust admission. The smallest node therefore remains useful without requiring a central server.

## Production boundary

The reference implementation intentionally does not claim production cryptography, network security, durable distributed consensus, or distributed atomicity. Those require audited providers, transport security, persistent protocol state, and interoperability testing. The production adapter contracts are interfaces for that work, not security guarantees by themselves.
