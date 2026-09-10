# FS Intermediate Representation

## Purpose

The FS Intermediate Representation (FS-IR) is the stable machine-readable boundary between semantic planning and backend-specific execution.

It prevents platform-specific APIs from leaking upward into intent and semantic layers.

## Layers

```text
Intent IR
   -> Requirement IR
   -> Plan IR
   -> Transaction IR
   -> Execution IR
   -> Observation IR
```

Each IR preserves ObjectIDs, semantic operation identity, dependencies, authority references, resource requirements, policy constraints and provenance.

## Backend Lowering

`FS-IR -> Backend Adapter -> Native/container/VM/distributed operation`

Lowering may change implementation but must preserve the declared semantic contract. Unsupported semantics cause explicit incompatibility rather than silent degradation.

## Static Validation

Before execution, FS-IR can be checked for:

- malformed references
- unsatisfied dependencies
- authority scope violations
- impossible resource requirements
- incompatible capabilities
- policy conflicts
- unsupported semantic operations
- unsafe cycles
- missing verification conditions

## Versioning

IR schemas are versioned independently from backend implementations. Compatibility requires explicit schema and semantic compatibility declarations.

## Security Boundary

FS-IR is not an authority token. Possessing a valid plan representation does not grant permission to execute it. Authority remains evaluated at the execution boundary.
