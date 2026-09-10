# FS Dependency Graph

## Purpose

The Dependency Graph models why an object or operation depends on another object, capability, resource, policy or service.

## Dependency types

```text
requires
provides
depends_on
conflicts_with
blocks
optional_dependency
runtime_dependency
policy_dependency
resource_dependency
```

Dependencies carry scope, version/compatibility constraints, health and provenance where applicable.

## Uses

The graph supports:

- feasibility analysis;
- startup ordering;
- safe shutdown;
- migration planning;
- failure impact analysis;
- resource placement;
- recovery ordering;
- package/environment resolution;
- simulation and what-if planning.

## Failure propagation

FS should distinguish direct failure from derived impact. A failed node may degrade an Environment; a degraded optional dependency may not. The graph provides the dependency path needed for impact analysis rather than treating every failure as global.

## Cycles

Cycles are valid in some domains but must be explicitly represented. Initialization and recovery require a strategy for strongly connected components rather than assuming a simple tree.

## Relationship to other graphs

Dependency Graph complements Object Graph, Capability Graph, Resource Graph and Reality Graph. These graphs should remain semantically distinct while supporting a unified query model in the future.
