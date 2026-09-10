# FS Capability Graph

## Purpose

The Capability Graph models what objects and resources can actually provide or consume. It connects logical requirements to verified capabilities without confusing capability discovery with authority.

## Example

```text
Application
  -> requires -> Linux
  -> requires -> Vulkan
  -> requires -> GPU
  -> requires -> 8 GiB RAM
  -> supports -> checkpoint

Computer
  -> provides -> Linux
  -> provides -> Vulkan
  -> provides -> GPU
  -> provides -> memory
  -> supports -> VM
```

Placement is valid only when requirements can be satisfied by admitted, healthy capabilities under policy.

## Capability classes

Capabilities may describe architecture, operating system, runtime, instruction sets, accelerators, devices, storage semantics, network properties, checkpoint/migration support, security features, isolation strength and application compatibility.

## Graph semantics

Relevant relationships include:

- `requires`
- `provides`
- `supports`
- `compatible_with`
- `incompatible_with`
- `depends_on`
- `delegates`
- `constrained_by`
- `failure_domain`

Capabilities should carry provenance, version, scope, confidence and verification state.

## Planner contract

The planner first determines feasibility, then optimizes among feasible candidates. It must account for locality, latency, bandwidth, reliability, failure domains, trust, resource cost and policy. A capability never grants permission by itself.

## Evolution

The Capability Graph is intended to become a common semantic layer for application mobility, universal runtime selection, virtual hardware, federation and recursive FS Computers.
