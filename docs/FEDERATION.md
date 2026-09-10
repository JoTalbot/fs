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

Every node has a stable cryptographic identity and a capability document. A node can be:

- LOCAL: the current machine;
- TRUSTED: an explicitly approved peer;
- DISCOVERED: visible but not yet trusted;
- QUARANTINED: known but blocked from participation;
- OFFLINE: previously known but currently unreachable.

## Discovery pipeline

```text
policy
  -> discover permitted peers
  -> receive capability advertisement
  -> verify identity/signature
  -> evaluate trust policy
  -> measure health/capacity
  -> add resource candidates
```

Discovery must never automatically grant execution, filesystem, device, or credential access.

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

Resource types include:

- storage;
- compute/CPU;
- memory;
- accelerator/GPU where supported;
- runtime;
- VM/container backend;
- network endpoint;
- device;
- backup/snapshot target.

## Resource planner

The planner selects resources using policy and observed state rather than a fixed machine list.

Inputs:

- workload requirements;
- data locality;
- trust level;
- capacity;
- health;
- latency/bandwidth;
- failure-domain diversity;
- cost/priority policy.

Outputs:

- placement plan;
- migration plan;
- replication plan;
- rejected candidates with reasons.

## Storage federation

A logical FS volume may use multiple approved nodes:

```text
                 logical volume
                /      |      \
             Node A  Node B  Node C
              shard   shard   parity
```

Erasure coding and replicas must preserve configured durability. Metadata must remain recoverable if one node disappears.

## Compute federation

An environment may request:

```yaml
resources:
  cpu: 4
  memory: 8GiB
  accelerator: optional
```

The planner can choose a local process, sandbox, container, microVM, or VM backend according to capabilities and policy.

## Neighbor discovery

Supported discovery transports should be implemented through adapters. Candidate mechanisms include local multicast/service discovery and explicitly configured rendezvous endpoints. The protocol must expose only FS capability metadata required for discovery.

No credential, private file listing, process inspection, or administrative control is implied by discovery.

## Trust establishment

Trust is explicit and cryptographically verifiable:

```text
DISCOVERED
   |
   v
VERIFY IDENTITY
   |
   v
POLICY DECISION
   |
   +----> REJECT
   |
   v
TRUSTED PEER
```

Trust can be revoked without deleting historical records.

## Federation operations

Future operations:

- `node discover`
- `node inspect`
- `node trust`
- `node revoke`
- `resource list`
- `resource plan`
- `environment place`
- `environment migrate`
- `volume replicate`
- `volume rebalance`
- `snapshot export`
- `snapshot import`

## Self-expansion principle

FS may continuously evaluate *permitted* resources and capabilities and propose or perform policy-approved optimization. It must not silently expand its authority. Every automatic federation action is logged with the initiating policy, selected resources, reason, result, and rollback/recovery information.
