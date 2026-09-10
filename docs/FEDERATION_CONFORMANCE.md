# Federation conformance and minimal initiator

The federation reference surface is now testable without a network, operating system discovery, or a specific cryptographic library.

## Conformance

`fs_overlay.conformance` contains versioned deterministic envelope vectors. A vector fixes the canonical envelope fields and expected SHA-256 digest. Implementations can use the vectors to detect serialization drift before interoperability testing.

`FederationEnvelope.to_bytes()` and `from_bytes()` provide a canonical transport payload with base64-encoded signatures. The transport is responsible for delivery and framing; the protocol owns semantic validation.

## Capability negotiation

`capability_negotiation.negotiate()` requires an identical protocol version and returns the sorted intersection of feature names. A protocol mismatch fails closed. Capabilities never grant authority.

## Key lifecycle

`KeyLifecycle` models ACTIVE, RETIRED and REVOKED key states. Rotation retires the previous active key; revocation prevents future use. It is a state contract, not a cryptographic implementation or secure key store.

## Minimal initiator

`MinimalInitiator` requires an explicit `BootstrapConfig`, `KeyProvider`, `FederationSigner`, `FederationTransport`, and local capabilities. It:

1. obtains the explicitly configured active key;
2. creates a deterministic advertisement envelope;
3. signs the unsigned envelope through the injected signer;
4. serializes the complete signed envelope;
5. hands it to the explicitly supplied transport and peer identifier.

It does not discover peers, open sockets, select carriers, modify host configuration, or grant trust.

The same reference contract can therefore be embedded by a server, desktop, mobile, ARM or IoT launcher. Platform-specific code belongs behind the capability and transport adapters.

## Production gate

The reference implementation is not a production federation stack. Before deployment, provide audited cryptography, authenticated/encrypted transport, secure key storage, persistent replay-state compaction, concurrency coordination, admission policy, failure-domain policy, interoperability testing across independent implementations, and operational recovery procedures.
