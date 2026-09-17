# Roadmap

## Phase 1 - storage and recovery foundations

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

## Phase 2 - execution and platform foundations

- [x] Linux isolation backend planning
- [x] Windows Job Objects backend
- [ ] macOS process/service backend
- [ ] POSIX/BSD baseline adapter
- [x] foreground runtime
- [ ] native service installers
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
- [ ] Linux adapter
- [ ] Windows adapter
- [ ] macOS adapter

## Phase 3 - execution semantics

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

- [x] Reed-Solomon implementation or audited dependency
- [x] metadata redundancy
- [x] self-healing
- [x] carrier quarantine
- [x] failure-domain aware placement
- [x] power-loss recovery tests
- [x] corruption/fuzz tests
- [x] workspace disaster recovery
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
