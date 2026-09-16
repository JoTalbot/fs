# Transport session re-authentication boundary reconnaissance

Date: 2026-09-16
Repository: `JoTalbot/fs`

## Scope

Focused review of the authenticated transport session gate for re-authentication, peer changes, provider failures, session closure, and sequence-state reset behavior. This is intentionally narrower than the earlier transport-boundary review and does not re-audit the provider implementation itself.

## Current contract

`src/fs_overlay/transport_gate.py` binds a gate instance to one `AuthenticatedPrincipal` and keeps independent send/receive monotonic sequence counters. Every `validate_session()`, `send()`, and `receive()` operation first checks that the injected provider is authenticated and that its current peer equals the bound principal.

A provider-side peer change therefore cannot silently become a valid session: the next gate operation fails closed, closes the provider, and raises `TransportSecurityError`. Provider errors while reading session state or performing I/O also invalidate the gate and attempt to close the provider.

The gate has no re-authentication or reset operation. Closing the gate permanently marks it closed, and a new authenticated session must be represented by a new gate instance. This prevents provider-side session replacement from implicitly inheriting the old gate's authorization and sequence state.

## Sequence/reset assessment

The gate does not reset sequence counters when the underlying provider reconnects or re-authenticates. That behavior is fail-closed rather than fail-open: a provider that resets its transport sequence while an existing gate remains alive will either be rejected by the provider or produce a sequence mismatch, rather than causing the gate to accept an unbound or replayed frame.

No repository-level path was found that lets a provider re-authenticate to a different peer and continue through the same gate without the peer-binding check. No reset API should be added to the generic gate without a concrete deployment contract defining authenticated session identity, sequence epoch semantics, and safe key/session rollover.

## Decision

No runtime change. The current gate is intentionally a one-session/one-principal boundary and does not invent production re-authentication semantics. Production qualification remains delegated to the concrete authenticated/encrypted transport provider and its deployment evidence.

## Evidence boundary

This reconnaissance establishes the fail-closed behavior of the repository gate only. It does not certify TLS/AEAD configuration, certificate or trust-root management, key custody, peer authentication implementation, or production deployment security.

## Next safe step

Do not modify the generic transport gate unless a concrete provider/deployment contract exposes a reproducible contract mismatch. Continue production-boundary reconnaissance only where it can identify a repository-level defect without fabricating deployment authority.
