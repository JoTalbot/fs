# FS Genesis Local Service

The Genesis Local Service is the smallest executable reference boundary between an FS node and the rest of the system.

## Boundary

```text
START
  -> identity
  -> capability observation
  -> admission
  -> ready
  -> semantic request
  -> loopback transport (optional)
  -> bounded backend
  -> observation
```

The service is intentionally not a general-purpose daemon framework. It does not listen on a network by itself, install persistence, elevate privileges, or modify host configuration.

The optional `GenesisServer` exposes the same service over a loopback-only framed TCP transport for local control-plane integration. It accepts only loopback bind addresses and inherits the transport message-size limit.

## Operations

- `ping`: readiness state.
- `identity`: stable node identity and protocol version.
- `capabilities`: current advertised capability snapshot.
- `admit`: explicit admission bound to the node identity.
- `execute`: bounded argv execution, available only after admission and only when an execution backend is configured.

## Security boundary

Admission is not authentication, capability is not permission, and execution is not automatically trusted. A production transport must add authenticated peer identity, authorization policy, leases, replay protection, quotas, audit records, and stronger isolation before remote execution is enabled.

The reference implementation deliberately keeps execution local and the optional transport loopback-only. This makes the vertical slice testable without turning the prototype into an accidental remote-command service, because humanity has suffered enough from those.

## Capability observation

`discover_local_capabilities()` returns a conservative host snapshot containing platform, architecture, CPU core count, and Linux memory information when available. Observation does not imply federation membership or permission to share those resources.

## CLI

The package entry point exposes inspection and a local server:

```bash
fs-overlay genesis ping
fs-overlay genesis identity
fs-overlay genesis capabilities
fs-overlay genesis serve --port 0
```

`genesis serve` binds only to loopback. Passing `--admit` explicitly moves the local service into the admitted state before serving requests.

## Next step

The next production-facing layer is a platform adapter that turns discovered capabilities into explicit offers and lowers admitted semantic operations into OS-native isolation such as Linux namespaces/cgroups or Windows Job Objects.
