# FS Roadmap

## Completion evidence rule

A checked item is a claim that the capability exists in the repository and is
exercised by tests. Every claim reconciled against implementation evidence is
registered in `tools/roadmap_evidence.py`, which binds the roadmap line to the
defining modules, the top-level symbols that constitute it, and the test files
that reference those symbols. `python tools/roadmap_evidence.py` (also executed
by `tests/test_roadmap_evidence.py`) fails when a claim loses its evidence.

Items without a registry entry are not yet reconciled: they may be partially
implemented, but no verified evidence has been recorded for them yet.

## Phase 0 - foundation

- [x] architecture
- [x] FSOV envelope specification
- [x] explicit carrier safety policy
- [x] managed workspace concept
- [x] minimal runtime concept
- [x] system-in-system execution model
- [x] unified FS object model
- [x] capability-aware runtime planner
- [x] control-plane architecture
- [x] bounded autonomy model
- [x] FS Constitution
- [x] four-space architecture: Data / Compute / Control / Resource
- [x] unified object state: desired / actual / health / identity / location
- [x] hierarchical reconciliation model
- [x] resource intelligence and capability graph concepts
- [x] immutable state and content lineage model
- [x] simulation / what-if / failure-injection architecture
- [x] security and supply-chain principles
- [x] FS Unified Computer architecture
- [x] Unified Resource Fabric concept
- [x] Universal Runtime concept
- [x] logical hardware profile and application mobility model
- [x] vertical FS stack from hardware/firmware to user intent
- [x] FS Hardware Abstraction Layer concept
- [x] FS Time Fabric concept
- [x] FS Reality Engine concept
- [x] FS Object Graph as system-wide model
- [x] hierarchical Meta Scheduler concept
- [x] Intent Layer concept
- [x] recursive Computer composition model
- [x] cross-cutting Security / Identity / Policy / Knowledge / Simulation / Observability / Recovery planes
- [x] Resource Ownership & Lease Layer concept
- [x] Causality & Time Fabric architecture
- [x] Capability Graph architecture
- [x] cross-space Transaction Engine architecture
- [x] universal State Machine Engine architecture
- [x] FS World Engine architecture
- [x] FS Semantic Kernel concept
- [x] Universal Object Contract
- [x] FS Execution Semantics
- [x] FS Authority Model
- [x] FS Provenance Engine concept
- [x] FS Dependency Graph concept
- [x] Intent-to-Reality Compiler concept
- [x] FS Knowledge Plane
- [x] FS Decision Engine
- [x] FS Learning & Adaptation Plane
- [x] FS Policy Compiler
- [x] FS Semantic ABI
- [x] FS World State Model
- [x] FS Unified Control Loop
- [x] FS Executable World Model
- [x] FS Computation Model
- [x] FS Plan DAG
- [x] FS Universal State Transition Machine
- [x] FS Intermediate Representation
- [x] FS executable semantic reference core
- [x] FS Genesis Bootstrap model
- [x] FS Resource Fabric admission model
- [x] FS Universal Session / Application Mobility model

## Phase 1 - local reference engine

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
- [ ] foreground runtime
- [ ] native service installers where appropriate
- [ ] local IPC control API
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
- [ ] failure-domain aware placement
- [ ] power-loss recovery tests
- [ ] corruption/fuzz tests
- [ ] workspace disaster recovery
- [x] transactional recovery journal
- [x] deterministic recovery planner
- [x] recovery graph
- [ ] failure injection suite
- [ ] reality snapshots
- [ ] confidence-aware observations
- [ ] provenance-aware recovery
- [ ] dependency-aware recovery ordering
- [ ] world-state recovery checkpoints
- [ ] transition-level compensation
- [ ] plan-level recovery
