# Security, Capabilities and Supply Chain

FS is designed around least authority, explicit trust and verifiable state.

## Capability-based access

Workloads should receive narrowly scoped capabilities rather than broad host privileges:

```text
filesystem.read(object-X)
volume.write(volume-Y)
device.use(device-Z)
network.connect(network-N)
```

Capabilities are policy-issued, auditable and revocable. Temporary capabilities may be represented as leases with expiration.

## Trust lifecycle

A node follows a distinct lifecycle:

```text
UNKNOWN → DISCOVERED → VERIFIED → TRUSTED
                         │
                         └→ QUARANTINED / REVOKED
```

Capability discovery never grants trust.

## Secrets

Configuration and manifests contain references such as `secret://db/main`, not raw credentials. Secret resolution belongs to a dedicated secret provider and policy boundary.

## Package supply chain

Environment packages should carry:

```text
manifest
version
content identity
dependencies
provenance
signature
compatibility requirements
```

Installation follows verify → policy check → stage → activate → verify. Failed activation must preserve the previous known-good state.

## Canary updates

Production environments can use copy-on-write canaries:

```text
production snapshot
       ↓
canary environment
       ↓
observe / validate
       ↓
promote or discard
```

## Learning and AI

Predictive or AI components may recommend placement, recovery, optimization or anomaly responses. They cannot create permissions, bypass policy, or directly expand authority.

The safe pipeline is:

```text
prediction
   ↓
policy validation
   ↓
safety governor
   ↓
transaction
   ↓
verification
```

## Formal invariants

Critical invariants should be expressed as machine-checkable properties and exercised with property-based tests, simulation and failure injection. Examples include:

```text
committed state → verified integrity
trusted node → verified identity
running workload → compatible runtime
committed shard → verified carrier write
```
