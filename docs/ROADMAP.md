# FS Overlay Roadmap

## Phase 1 - storage foundation

- [x] manifest model
- [x] deterministic chunker
- [x] authenticated encryption interface
- [x] erasure-coding interface
- [x] carrier adapter interface
- [x] atomic append protocol
- [x] inventory database with redundant recovery records
- [x] content-addressed object store
- [x] Merkle DAG implementation
- [x] event log
- [x] audit command
- [x] recovery command
- [x] transaction engine implementation
- [x] state/reconciliation engine implementation
- [x] resource ownership/lease primitives
- [x] causal event metadata
- [x] universal object contract implementation
- [x] provenance records
- [x] dependency graph primitives
- [x] knowledge record primitives
- [x] decision record primitives
- [x] world-state snapshot primitives
- [x] unified control-loop primitives
- [x] computation/transition primitives
- [x] Plan DAG representation
- [x] universal state transition primitives
- [x] FS-IR schema and validation
- [x] Genesis node primitives
- [x] capability matching engine
- [x] application session primitives
- [x] presentation endpoint primitives
- [x] localhost semantic transport
- [x] node identity primitive
- [x] bounded native process adapter

## Phase 2 - cross-platform runtime

- [x] Linux isolation backend planning
- [ ] Linux adapter
- [ ] Windows adapter
- [ ] macOS adapter
- [ ] POSIX/BSD baseline adapter
- [x] foreground runtime
- [ ] native service installers where appropriate
- [x] local IPC control API
- [x] structured JSON logs
- [x] conservative local capability discovery
- [x] capability negotiation
- [x] hardware abstraction adapter
- [x] hardware capability fingerprint
- [x] platform time adapter
- [x] monotonic/logical time adapter
- [x] semantic ABI adapters
- [x] semantic verification adapters
- [x] FS-IR backend lowering
- [x] Genesis bootstrap executable
- [x] local node identity store
- [x] platform capability adapter baseline
- [x] versioned backend contracts

## Phase 3 - managed workspaces

- [x] workspace registration
- [x] workspace health state
- [x] migration/import workflow
- [ ] observed mode
- [ ] managed mode
- [ ] detach/export workflow
- [ ] adaptive carrier placement
- [ ] content-addressed workspace state
- [x] workspace snapshots
- [x] transactional rollback
- [ ] copy-on-write snapshots
- [ ] environment branching
- [ ] environment diff/merge
- [ ] historical/time-travel views
- [ ] provenance-aware workspace history

## Phase 4 - execution runtime

- [x] declarative workload model
- [ ] process supervisor
- [ ] resource policy engine
- [ ] restart/recovery policies
- [ ] native process backend
- [ ] Linux namespaces/cgroups backend
- [ ] Windows Job Objects backend
- [ ] macOS process/service backend
- [ ] capability-based filesystem access
- [ ] workload lifecycle API
- [ ] resource reservations
- [x] resource lease planning contract
- [ ] resource leases
- [ ] workload priorities
- [ ] data-locality-aware placement
- [ ] universal application manifest
- [ ] universal execution API
- [ ] application compatibility matrix
- [ ] execution semantics adapter contract
- [ ] authority enforcement
- [ ] policy-compiled execution constraints
- [ ] decision-gated execution planning
- [ ] transition precondition/postcondition enforcement
- [ ] idempotent operation semantics
- [ ] plan execution coordinator
- [ ] application mobility coordinator
- [ ] remote presentation transport

## Phase 5 - resilience

- [ ] Reed-Solomon implementation or audited dependency
- [ ] metadata redundancy
- [x] self-healing
- [x] carrier quarantine
- [x] failure-domain aware placement
- [ ] power-loss recovery tests
- [ ] corruption/fuzz tests
- [ ] workspace disaster recovery
- [x] transactional recovery journal
- [x] deterministic recovery planner
- [x] recovery graph
- [x] failure injection suite
- [ ] reality snapshots
- [ ] confidence-aware observations
- [ ] provenance-aware recovery
- [ ] dependency-aware recovery ordering
- [ ] world-state recovery checkpoints
- [ ] transition-level compensation
- [ ] plan-level recovery
