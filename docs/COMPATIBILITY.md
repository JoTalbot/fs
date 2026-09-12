# Compatibility and Version Policy

V1 uses an explicit protocol-version gate. Federation peers must advertise the same protocol version before capabilities are negotiated or federation messages are admitted.

## Policy

- The protocol version is an integer carried by `NodeIdentity`, `BootstrapConfig`, and federation advertisements.
- V1 is protocol version `1`.
- Version mismatch fails closed. There is no implicit downgrade, best-effort parsing, or automatic cross-version authority.
- A matching version does not grant authority. Trust admission, signature verification, replay protection, and capability negotiation remain separate gates.
- Capability negotiation returns the deterministic sorted intersection of features offered by both peers.
- Adding an optional feature does not change the protocol version when the existing wire and security contract remains compatible.
- A change that alters signed fields, envelope semantics, admission rules, persistence semantics, or other interoperability/security contracts requires a new protocol version.
- Unknown future versions must be rejected rather than guessed at.

## Compatibility procedure

1. Read the peer's advertised protocol version.
2. Require exact equality with the local supported version.
3. Negotiate only the intersection of declared capabilities.
4. Perform explicit trust and signature admission independently of capabilities.
5. Persist only envelopes that pass authentication, freshness/replay, and durable admission checks.

This policy deliberately favors a boring failure over a clever compatibility heuristic. Distributed systems have enough opportunities to become haunted without adding one more.

## V1 release evidence

Executable tests cover exact-version acceptance, version mismatch rejection, deterministic feature intersection, and the rule that capabilities do not grant authority. The minimal two-node federation test also exercises a signed advertisement through transport-neutral serialization and durable admission/recovery.
