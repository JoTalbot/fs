# FS Semantic ABI

## Purpose

The Semantic ABI is the stable interoperability boundary between FS applications, runtimes, environments, logical Computers and Worlds.

It defines semantic contracts rather than implementation details. A backend may differ internally while preserving the declared observable contract.

## Contract Domains

- object identity and lifecycle
- desired/actual state
- capabilities
- authority references
- resources and reservations
- execution operations
- events and causal metadata
- provenance
- errors and uncertainty
- snapshot/checkpoint semantics
- migration/import/export semantics

## Compatibility

Compatibility is evaluated by contract version and declared semantic capabilities, not by platform name alone.

An implementation must explicitly declare unsupported semantics. It must not claim compatibility merely because an API call exists.

## Portability

The same logical object may move across Linux, Windows, macOS, containers, VMs or federated nodes when the target backend satisfies its semantic requirements.

Implementation-specific extensions are namespaced and cannot silently redefine core semantics.
