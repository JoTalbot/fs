# Distributed FS Future Architecture

The local runtime is the first implementation of a broader architecture in which the same control plane can manage multiple physical nodes.

## Node model

A node exposes:

- capabilities;
- resources;
- storage pools;
- isolation backends;
- network endpoints;
- health state.

The control plane can remain local or become a cluster coordinator. The object model does not need to change.

## Logical versus physical resources

```text
logical Environment
        |
        +---- logical Volume
        |          |
        |          +---- physical shard/node A
        |          +---- physical shard/node B
        |
        +---- Process placement
                   |
                   +---- node A
```

Placement is a policy decision rather than an identity change.

## Failure domains

The scheduler should understand domains such as:

```text
node -> rack -> zone -> site
```

Erasure-coded storage and replicas should prefer independent domains so one physical failure does not remove several logical shards at once.

The same concept applies to execution. A highly available service can place instances on independent nodes when policy permits.

## Control-plane consistency

The initial implementation is single-node. A future clustered control plane can introduce:

- replicated metadata log;
- leader election;
- quorum-based state publication;
- distributed leases;
- fencing for failed nodes;
- resumable reconciliation.

The storage engine must not assume that a distributed database always exists. Local recovery remains a supported mode.

## Distributed object identity

Object UUIDs remain globally unique. Generations increase monotonically per object. Events carry a correlation ID and node ID.

Conflict resolution must be explicit. Silent last-writer-wins is inappropriate for authoritative system state.

## Data plane versus control plane

The architecture separates:

```text
Control plane
  policy, placement, desired state, identity, recovery

Data plane
  file content, chunks, streams, VM disks, network traffic
```

This separation permits the control plane to move from local orchestration to a distributed scheduler without redesigning the logical storage model.

## Eventual super-system

The strongest future form is a portable system control plane capable of managing:

- local and remote storage;
- native processes;
- sandboxes and containers;
- microVMs and VMs;
- virtual networks;
- package/runtime environments;
- snapshots and recovery;
- multiple physical nodes.

At that point, FS is better understood as a **portable system substrate** than as a conventional filesystem.

The term "super-system" is architectural language, not a claim that an ordinary user-space installation can override a host kernel. Stronger authority comes from explicit boot, hypervisor and hardware mechanisms.
