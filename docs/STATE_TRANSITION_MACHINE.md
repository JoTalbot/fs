# FS State Transition Machine

## Purpose

This specification gives every managed FS object a common transition semantics while allowing object-specific states and backend implementations.

## Transition

`StateTransition = (Object, From, Trigger, Preconditions, Policy, Authority, Effects, Verification, To, Evidence)`

A transition is accepted only when all declared preconditions and authorization checks pass.

## Canonical Lifecycle

```text
DECLARED
  -> ADMITTED
  -> PREPARED
  -> ACTIVE
  -> OBSERVED
  -> VERIFIED
  -> RETIRED
```

Failure and exceptional states include `DEGRADED`, `BLOCKED`, `QUARANTINED`, `RECOVERING`, `FAILED` and `UNKNOWN`.

Objects may define narrower lifecycle states, but they must preserve the meaning of the universal lifecycle contract.

## Transition Guards

Guards may depend on:

- object state
- dependency state
- capability evidence
- authority
- resource lease
- policy
- time/deadline
- integrity
- provenance
- observed reality

Guards are evaluated before effects are applied.

## Verification

A requested transition and an observed transition are distinct. The object enters a verified state only after the Reality Engine observes sufficient evidence that the declared postcondition holds.

## Recovery

Recovery is itself a state transition and therefore follows the same policy, authority, resource and verification rules. There is no privileged invisible recovery path.

## Recursive Semantics

A World, Computer, Environment, Application and resource object can all use the same transition structure. Parent transitions may coordinate child transitions but cannot silently erase their constraints.
