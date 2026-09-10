# Federation interoperability and conformance

FS treats interoperability as a separate validation boundary from the internal Python test suite.

## Conformance layers

1. **Canonical serialization**: an implementation must reproduce the versioned envelope bytes and digest for the published vectors.
2. **Admission semantics**: implementations must reject malformed, stale, future, replayed, reordered, unsigned, and invalidly signed messages according to the protocol contract.
3. **Trust semantics**: discovery observations never grant authority; node and key admission remain explicit policy decisions.
4. **Durable semantics**: accepted message IDs and sender sequence high-water marks must survive restart and concurrent writers must converge on one authoritative admission decision.
5. **Adapter semantics**: production transports, key stores, and admission backends must expose the required contracts without weakening the protocol invariants.

## Independent implementation requirement

A conformance run is strongest when the vectors are consumed by an implementation other than the code that generated them. The reference Python implementation may validate the vectors against itself for regression coverage, but that is not evidence of independent interoperability.

An independent harness should treat the vector files as data, not import FS implementation internals to derive expected values. For each vector it should report `pass`, `fail`, or `unsupported`, with the protocol version and vector identifier recorded in the result.

## Negative cases

The interoperability suite should include at minimum:

- changed payload with an unchanged signature;
- changed sender identity;
- changed sequence number;
- duplicate message ID;
- sender sequence rollback;
- stale timestamp;
- future timestamp outside the accepted clock skew;
- missing signature;
- unknown/revoked key;
- unexpected node/key fingerprint;
- unsupported protocol version;
- malformed canonical envelope;
- ambiguous durable commit result.

A conforming implementation must fail closed for cases where the protocol requires rejection. It must not turn an unsupported security property into an implicit fallback.

## Versioning

Conformance vectors are versioned with the federation protocol. Changes to canonical serialization, required fields, replay rules, or security-sensitive semantics require a new vector/version set and an explicit compatibility decision.

Implementations should report the exact vector version they support. Unknown future protocol versions must not be silently interpreted as the current version.

## Production qualification

Passing conformance vectors does not certify cryptography, transport security, filesystem semantics, database durability, or operational recovery. Production qualification additionally requires audited cryptographic providers, authenticated transport, secure key storage, authoritative admission, backend-specific crash/recovery testing, and review against the deployment failure model.
