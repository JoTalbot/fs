# Unified FS Namespace

The long-term FS namespace presents storage and execution as one logical graph while keeping physical host paths as implementation details.

## Namespace roots

```text
fs:///
├── system/
│   ├── capabilities
│   ├── policies
│   └── events
├── workspaces/
│   └── <workspace>/
├── volumes/
│   └── <volume>/
├── environments/
│   └── <environment>/
├── packages/
├── snapshots/
└── devices/
```

This is a logical namespace, not necessarily a mounted POSIX filesystem. A future provider may expose selected parts through FUSE, WinFsp, macFUSE or another supported mechanism, but the control-plane model must not depend on a mount.

## Content identity

Stable object identity and content identity are separate:

```text
object ID = identity of the logical resource
content ID = hash of immutable content
```

Content-addressed immutable state enables deduplication, integrity validation, snapshot sharing and migration.

## Namespace operations

Core semantic operations:

```text
lookup(path)
read(object)
write(object, generation)
create(type, spec)
delete(object)
snapshot(object)
restore(snapshot)
link(parent, child)
unlink(parent, child)
```

Every mutating operation goes through authorization and generation checks.

## Host mapping

A workspace may map to an explicit host directory:

```yaml
workspace: demo
source: /srv/projects/demo
mode: managed
```

The host path remains visible and controllable by the operator. FS does not require a hidden system-wide namespace translation layer.

## Snapshots

Snapshots reference immutable generations. A snapshot should be cheap to create because it records references rather than copying unchanged data.

A future storage engine can use copy-on-write, deduplication and erasure-coded chunks underneath the same namespace.

## Transactions

Namespace changes should support small atomic transactions:

```text
BEGIN
  create A
  link A -> parent
  update manifest
COMMIT
```

On failure, the transaction is either committed as a complete generation or rolled back to the last verified state.

## Virtual system tree

As FS grows into a system layer, the namespace can expose execution objects beside files:

```text
fs:///environments/game/processes/server
fs:///environments/game/services/matchmaker
fs:///environments/game/networks/private
fs:///environments/game/devices/gpu0
fs:///environments/game/snapshots/42
```

This unifies inspection without pretending that every resource is literally a file.
