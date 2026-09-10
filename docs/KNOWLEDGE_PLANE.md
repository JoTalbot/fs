# FS Knowledge Plane

## Purpose

The Knowledge Plane stores structured, provenance-aware knowledge used by planning, scheduling, recovery and explanation. It is not the source of truth for reality.

## Knowledge vs Reality

- Reality is the observed/verified state of objects, resources and execution.
- Knowledge is a model derived from observations, history, specifications, simulations and external declarations.
- Every material knowledge item carries provenance, confidence, freshness and scope.
- Stale or conflicting knowledge must not silently override fresh verified observations.

## Knowledge Classes

- fact
- observation
- capability claim
- limitation
- dependency inference
- compatibility statement
- historical pattern
- performance estimate
- failure pattern
- policy interpretation
- uncertainty

## Lifecycle

`Acquire -> Normalize -> Validate -> Attribute -> Score Confidence -> Store -> Retrieve -> Revalidate -> Retire`

Knowledge may be invalidated without rewriting immutable historical provenance.

## Safety

Knowledge can inform decisions but cannot grant authority, permissions or leases. Unknown knowledge is uncertainty, not permission.
