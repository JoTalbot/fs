# FS Authority Model

## Purpose

The Authority Model defines who or what may cause a state transition and how that authority is bounded. Capability describes possibility; authority describes permission.

## Authority chain

```text
Principal
  -> Identity
  -> Policy
  -> Delegation
  -> Resource Lease / Scope
  -> Operation
  -> Target Object
```

An operation is valid only when the complete chain permits it.

## Properties

Authority should be:

- explicit;
- scoped;
- time-bounded where appropriate;
- revocable;
- attributable;
- auditable;
- non-escalating through delegation;
- independent from mere discovery.

## Principals

Potential principals include the operator, local FS runtime, a managed Environment, a trusted federation node or an approved automation policy. AI-assisted planning is a planning mechanism, not an independent authority principal unless explicitly modeled and authorized.

## Delegation

Delegation may narrow authority but cannot expand the delegator's maximum scope. A child Computer or Environment inherits only the capabilities and permissions explicitly delegated to it.

## Decision

```text
Can the operation be performed?
  1. Identify principal
  2. Verify identity
  3. Evaluate policy
  4. Check capability
  5. Check lease/scope
  6. Check object state
  7. Check transaction constraints
  8. Approve or deny
```

## Revocation and failure

Revocation must prevent new use as quickly as the backend can guarantee. Existing operations follow their declared cancellation, completion or recovery semantics. Ambiguous authority must fail closed for high-impact operations.

## Safety boundary

This model is designed to make FS more capable without creating implicit privilege escalation. Host and federation boundaries remain explicit.
