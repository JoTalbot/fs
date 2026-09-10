# Durable admission backend requirements

`DurableFederationState` separates protocol admission from the storage mechanism used to serialize and persist that decision. The core contract is intentionally small: a deployment must prevent concurrent writers from admitting conflicting replay state and must define what happens when persistence fails.

## Reference file coordination

`FileAdmissionCoordinator` is appropriate for a local process group when the underlying filesystem provides the expected OS locking semantics. It serializes the admission critical section and lets a crashed process release its lock through normal descriptor/OS cleanup.

It does **not** provide a transaction between the lock and the journal, and it does not provide distributed consensus, a lease service, or a database transaction. A successful lock acquisition therefore must not be described as an ACID commit.

## Transactional backend boundary

A stronger deployment can implement `DurableAdmissionCoordinator` over a transactional store or another authoritative coordination service. Such an implementation should define all of the following explicitly:

1. **Serialization scope**: which resource or partition is mutually exclusive.
2. **Commit boundary**: which admission decision and durable state changes become visible together.
3. **Failure semantics**: what happens when the process dies before, during, or after commit.
4. **Recovery semantics**: how incomplete work is detected and reconciled after restart.
5. **Ordering**: how sender sequence high-water marks and message IDs are made authoritative.
6. **Durability**: what acknowledgement means and which storage failures can still lose data.
7. **Concurrency model**: whether multiple processes, hosts, or regions can participate safely.
8. **Clock policy**: whether freshness is evaluated locally or against an authoritative time source.
9. **Retention/compaction**: how replay history is compacted without weakening duplicate or rollback protection.
10. **Auditability**: how the accepted decision remains attributable to the authenticated sender and durable event.

## Required invariant

For every admitted envelope, the deployment must preserve this invariant:

```text
authenticated + trusted + fresh envelope
        |
        v
one authoritative admission decision
        |
        +--> durable replay state
        |
        +--> durable audit record
```

The reference implementation uses an append-only event journal plus an optional coordinator. That is a reference architecture, not a universal transactional guarantee. Production systems should select a backend whose atomicity and recovery properties match the actual failure model.

## Fail-closed rule

If the coordinator cannot establish its required critical section, durable admission must not continue. If the durable backend reports an ambiguous commit result, the deployment must resolve that ambiguity from authoritative durable state before treating the message as admitted again.

The reference tests model one important ambiguity explicitly: the journal append can complete while the caller loses its acknowledgement before in-memory admission indexes are updated. In that case the current process deliberately does **not** infer success from the exception path. A fresh `DurableFederationState` rebuilds its replay indexes from the journal, making the persisted event the authoritative basis for deciding whether a retry is a duplicate. This is a recovery test, not a claim that the reference journal is a transactional database.

## Interoperability boundary

A production backend should be tested independently against the federation conformance vectors and replay invariants. Passing the Python test suite demonstrates implementation behavior for the tested adapter; it does not establish interoperability with an independent implementation or certify the backend's security properties.
