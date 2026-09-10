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
  -> bounded backend
  -> observation
```

The service is intentionally not a general-purpose daemon framework. It does not listen on a network by itself, install persistence, elevate privileges, or modify host configuration.

## Operations

- `ping`: readiness state.
- `identity`: stable node identity and protocol version.
- `capabilities`: current advertised capability snapshot.
- `admit`: explicit admission bound to the node identity.
- `execute`: bounded argv execution, available only after admission and only when an execution backend is configured.

## Security boundary

Admission is not authentication, capability is not permission, and execution is not automatically trusted. A production transport must add authenticated peer identity, authorization policy, leases, replay protection, quotas, audit records, and stronger isolation before remote execution is enabled.

The reference implementation deliberately keeps execution local. This makes the vertical slice testable without turning the prototype into an accidental remote-command service, because humanity has suffered enough from those.

## Next step

The local service becomes the semantic endpoint behind a localhost transport. The following production-facing layer is a platform adapter that discovers capabilities and lowers admitted semantic operations into OS-native mechanisms such as Linux namespaces/cgroups or Windows Job Objects.
