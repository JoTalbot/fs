# Transport Provider Boundary Reconnaissance — 2026-09-16

## Question

Does the implemented `AuthenticatedTransport` / `FailClosedTransportGate` boundary contain a reproducible fail-open semantic defect beyond the previously audited session binding and re-authentication boundary?

## Repository evidence

Reviewed current `main` state at base `cdc87f1e0a874610abf4962d72e32004e53bc327`:

- `src/fs_overlay/production_adapters.py`
  - `AuthenticatedTransport` is an injected provider boundary.
  - The contract exposes authentication state, peer identity, send/receive, and close operations but does not claim to implement TLS, AEAD, certificates, trust roots, or key custody.
- `src/fs_overlay/transport_gate.py`
  - Requires the provider session to report authenticated state.
  - Requires the provider peer to equal the already authenticated principal node.
  - Closes the session on provider state, send, receive, authentication, peer, malformed-frame, and sequence/replay failures.
  - Enforces local monotonic frame sequence numbers.
  - Does not implement cryptography itself.
- `src/fs_overlay/executor_preflight.py`
  - Checks identity, policy, exact transfer authority bindings, live revocation, and prepared journal state before validating the transport session.
  - The current path does not grant host filesystem mutation capability.
- `tests/test_transport_gate.py` and `tests/test_executor_preflight.py`
  - Cover authentication loss, peer substitution, provider state/send/receive failures, malformed frames, replay/sequence violations, and the requirement that revoked authority does not touch the transport.
- Adapter conformance references require an injected transport to expose authenticated state and reject invalid authentication input.

## External research

- RFC 8446 (TLS 1.3) defines the protocol behavior for authenticated encrypted transport and connection closure. The specification distinguishes protocol semantics from application-layer handling; it does not by itself qualify a deployment.
- OWASP Transport Layer Security guidance recommends TLS 1.3 by default, modern AEAD suites, correct certificate validation, protected private keys, and explicit mutual TLS where client authentication is required.
- OWASP Web Service Security guidance requires well-configured TLS for sensitive authenticated service traffic and emphasizes server certificate validation and mutual TLS where appropriate.
- An external `security-review` Agent Skill was inspected as an untrusted methodology reference. Its relevant review themes are trust-boundary analysis, authentication/authorization checks, data protection, configuration risk, and evidence of error handling. It does not override the FS security contract.

## Decision

No repository-level fail-open defect was reproduced.

The `AuthenticatedTransport` protocol is intentionally a deployment/provider boundary. Implementing generic TLS, certificate validation, trust-root management, mTLS policy, private-key custody, or cipher-suite configuration inside FS core would invent deployment-specific security authority and would not constitute production qualification.

The frame sequence checks in `FailClosedTransportGate` are an application-layer replay/ordering control. They are not a substitute for the authenticated/encrypted transport provider and must not be described as such.

The executor's current transport ordering is fail-closed: transport validation occurs only after identity, policy, authority, revocation, and journal checks. The provider is therefore not contacted by the preflight path when those earlier gates fail.

## What remains unproven

Production qualification still requires evidence from the concrete transport provider and deployment, including the selected TLS/secure-channel protocol and version, authentication/trust configuration, key custody and lifecycle, peer authorization policy, failure/restart behavior, exact dependency/build provenance, and required independent security review.

Semantic CI coverage of the FS transport gate cannot certify those deployment properties.

## Result

No runtime implementation change is justified by this reconnaissance. Preserve the explicit provider boundary and the existing V1 production blocker rather than adding speculative transport security machinery.

## Next safe step

Perform one fresh reconnaissance of another still-unqualified production boundary. Modify code only if a concrete repository-level contract mismatch is reproducibly demonstrated.