# FS Policy Compiler

## Purpose

The Policy Compiler transforms human-readable policy intent into explicit, machine-checkable constraints used by authority, admission, planning and execution layers.

## Pipeline

`Policy Intent -> Parse -> Normalize -> Type Check -> Constraint IR -> Conflict Analysis -> Verification -> Signed/Versioned Policy`

## Policy Properties

Policies are:

- scoped
- versioned
- attributable
- composable where semantics permit
- conflict-detectable
- revocable
- auditable

A lower-level policy may narrow an upper-level policy but may not silently broaden authority.

## Constraint Classes

- identity and authority
- resource limits
- placement
- data locality
- network
- device access
- execution backend
- lifecycle
- security
- recovery
- autonomy budget
- federation trust

## Safety

Ambiguous or contradictory policies fail closed for affected operations. Compilation never creates permissions that are absent from the Authority Model.
