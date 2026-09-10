# FS Federation and Resource Discovery

## Purpose

FS can grow from a single-machine control plane into a federation of explicitly trusted FS nodes. A node may advertise capabilities such as storage capacity, compute capacity, supported runtimes, virtualization backends, network reachability, and availability.

Discovery is a capability-discovery mechanism, not a license to inspect or modify neighboring systems. Discovery is limited to networks, peers, and resources explicitly permitted by policy.

## Node model

```text
FS Node
  identity
  capabilities
  resources
  environments
  policy
  health
  trust state
```

Every node has a stable identity and a capability document. Cryptographic identity is represented by a provisioned public-key fingerprint; signature verification is an injected verifier so the core does not invent cryptography. A node can be LOCAL, TRUSTED, DISCOVERED, QUARANTINED, or OFFLINE.

## Discovery and trust pipeline

```text
policy
  -> discover permitted peers
  -> receive capability advertisement
  -> verify advertisement signature
  -> match identity fingerprint against explicit trust
  -> reject stale observations
  -> evaluate health/capacity
  -> add resource candidates
```

Unknown, unsigned, stale, revoked, or fingerprint-mismatched advertisements are rejected. Discovery never automatically grants execution, filesystem, device, credential, or administrative access.

## Resource abstraction

A resource is described independently from its physical location:

```text
Resource
  id
  node
  type
  capacity
  available
  capabilities
  performance hints
  failure domain
  trust level
  policy constraints
```

Resource types include storage, compute/CPU, memory, accelerator/GPU where supported, runtime, VM/container backend, network endpoint, device, and backup/snapshot target.

## Resource planner

The planner selects resources using policy and observed state rather than a fixed machine list. Inputs include workload requirements, data locality, trust, capacity, health, latency/bandwidth, failure-domain diversity, and cost/priority policy.

## Storage federation and reconciliation

A logical FS volume may use multiple approved nodes. The reference `FederationReconciler` produces deterministic replica-repair decisions from trusted node observations. It does **not** copy data or open network connections. A separate authorized executor must apply each decision and provide post-action evidence.

```text
trusted observations
        |
        v
desired replica count
        |
        v
 deterministic plan
        |
        v
explicit executor
        |
        v
verification / recovery
```

Erasure coding and replicas must preserve configured durability. Metadata must remain recoverable if one node disappears.

## Minimal initiator

`MinimalBootstrap` provides the smallest useful local initiation path: create an explicitly selected FS root and an atomic node configuration containing a generated or operator-supplied node identifier. It does not scan the host, install services, open ports, or discover peers automatically.

The intended bootstrap progression is:

```text
one command/action on a permitted resource
        -> explicit FS root
        -> local node identity
        -> capability advertisement
        -> operator/policy trust
        -> optional federation participation
```

This makes a tiny local initiator compatible with later expansion without giving the initial process authority over the surrounding machine.

## Federation operations

Implemented reference primitives now cover:

- explicit trust entries and revocation;
- signed-advertisement verification boundary;
- monotonic advertisement observations;
- trusted-node directory;
- deterministic replica-repair planning;
- atomic minimal bootstrap configuration.

Network discovery, real cryptographic key management, transport authentication, remote copy, distributed consensus, and distributed transactions remain explicit adapters/protocol work. They are not simulated as completed merely because a Python object can describe them.

## Self-expansion principle

FS may continuously evaluate *permitted* resources and capabilities and propose or perform policy-approved optimization. It must not silently expand its authority. Every automatic federation action is logged with the initiating policy, selected resources, reason, result, and rollback/recovery information.
