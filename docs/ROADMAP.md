# FS Roadmap

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

## Phase 1 - local reference engine

- [ ] manifest model
- [ ] deterministic chunker
- [ ] authenticated encryption interface
- [ ] erasure-coding interface
- [ ] carrier adapter interface
- [ ] atomic append protocol
- [ ] inventory database with redundant recovery records
- [ ] content-addressed object store
- [ ] Merkle DAG implementation
- [ ] event log
- [ ] audit command
- [ ] recovery command
- [ ] transaction engine
- [ ] state/reconciliation engine

## Phase 2 - cross-platform runtime

- [ ] Linux adapter
- [ ] Windows adapter
- [ ] macOS adapter
- [ ] POSIX/BSD baseline adapter
- [ ] foreground runtime
- [ ] native service installers where appropriate
- [ ] local IPC control API
- [ ] structured JSON logs
- [ ] capability discovery
- [ ] capability negotiation
- [ ] versioned backend contracts
- [ ] hardware abstraction adapter
- [ ] hardware capability fingerprint
- [ ] platform time adapter

## Phase 3 - managed workspaces

- [ ] workspace registration
- [ ] workspace health state
- [ ] migration/import workflow
- [ ] observed mode
- [ ] managed mode
- [ ] detach/export workflow
- [ ] adaptive carrier placement
- [ ] content-addressed workspace state
- [ ] workspace snapshots
- [ ] transactional rollback
- [ ] copy-on-write snapshots
- [ ] environment branching
- [ ] environment diff/merge
- [ ] historical/time-travel views

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
- [ ] resource leases
- [ ] workload priorities
- [ ] data-locality-aware placement
- [ ] universal application manifest
- [ ] universal execution API
- [ ] application compatibility matrix

## Phase 5 - resilience

- [ ] Reed-Solomon implementation or audited dependency
- [ ] metadata redundancy
- [ ] self-healing
- [ ] carrier quarantine
- [ ] failure-domain aware placement
- [ ] power-loss recovery tests
- [ ] corruption/fuzz tests
- [ ] workspace disaster recovery
- [ ] transactional recovery journal
- [ ] deterministic recovery planner
- [ ] recovery graph
- [ ] failure injection suite
- [ ] reality snapshots
- [ ] confidence-aware observations

## Phase 6 - isolation platform

- [ ] container backend where available
- [ ] sandbox backend where available
- [ ] microVM backend research
- [ ] VM backend research
- [ ] virtual disk stored in FS container
- [ ] guest lifecycle manager
- [ ] host-independent workspace import/export
- [ ] migration protocol
- [ ] live migration where supported
- [ ] virtual hardware fabric
- [ ] virtual device model

## Phase 7 - FS control plane

- [x] unified object/policy model foundation
- [x] control-plane reconciliation concept
- [ ] virtual filesystem namespace
- [ ] network policy abstraction
- [ ] device/resource policy abstraction
- [ ] package/runtime environment manager
- [ ] multi-environment orchestration
- [ ] host OS as managed guest option
- [ ] boot/runtime integration research
- [ ] event bus
- [ ] state graph
- [ ] desired/actual state reconciler
- [ ] hierarchical reconciler
- [ ] unified observability
- [ ] policy compiler
- [ ] safety governor
- [ ] explainable decision records
- [ ] autonomy budgets
- [ ] intent API
- [ ] object graph engine
- [ ] reality engine
- [ ] meta-scheduler

## Phase 8 - federation and resource mesh

- [ ] FS node identity
- [ ] signed capability advertisements
- [ ] permitted peer discovery
- [ ] explicit trust establishment/revocation
- [ ] resource graph
- [ ] capability graph
- [ ] storage federation
- [ ] trusted compute federation
- [ ] failure-domain aware distributed placement
- [ ] remote environment placement
- [ ] environment migration
- [ ] federation-wide snapshots
- [ ] automatic resource rebalancing
- [ ] offline-first reconciliation
- [ ] resource reservations across nodes
- [ ] capability leases across nodes
- [ ] network-aware placement
- [ ] energy/thermal-aware placement
- [ ] recursive Computer federation
- [ ] cross-Computer scheduling

## Phase 9 - autonomous optimization

- [ ] autonomy levels L0-L4
- [ ] policy-bounded decision engine
- [ ] placement scoring engine
- [ ] health-driven remediation
- [ ] capacity forecasting
- [ ] predictive maintenance signals
- [ ] automatic recovery planning
- [ ] predictive risk engine
- [ ] data gravity optimization
- [ ] resource market / internal resource matching
- [ ] AI-assisted planning under policy control
- [ ] audit trail for every autonomous action
- [ ] safe-stop on uncertain decisions
- [ ] shadow planning
- [ ] what-if simulation
- [ ] confidence scoring
- [ ] intent-driven autonomous planning
- [ ] hierarchical scheduling optimization

## Phase 10 - simulation and digital twin

- [ ] FS simulation backend
- [ ] node digital twins
- [ ] FS World digital twin
- [ ] deterministic event replay
- [ ] scenario runner
- [ ] failure injection
- [ ] state time travel
- [ ] branch/compare/promote workflow
- [ ] predictive impact analysis
- [ ] full Object Graph simulation
- [ ] hardware/resource simulation
- [ ] time-fabric simulation

## Phase 11 - production

- [ ] security review
- [ ] threat model
- [ ] performance benchmarks
- [ ] Windows/Linux/macOS CI matrix
- [ ] signed releases
- [ ] upgrade/rollback mechanism
- [ ] disaster-recovery documentation
- [ ] compatibility test suite
- [ ] federation interoperability tests
- [ ] supply-chain verification
- [ ] canary update mechanism
- [ ] formal/property-based invariant tests
- [ ] hardware compatibility certification
- [ ] runtime compatibility certification
- [ ] end-to-end intent-to-execution tests

## Guiding rules

1. FS must preserve host functionality unless the operator explicitly selects an isolated/system deployment.
2. Every automatic action must be attributable, reversible where practical, constrained to an explicit workspace/root, and validated after the fact.
3. Adaptability increases compatibility; it never silently expands authority.
4. The resident daemon remains minimal. Heavy capabilities are workers/modules.
5. Stronger-than-host isolation requires explicit platform mechanisms such as containers, sandboxes, microVMs or VMs.
6. FS must never claim a recovery or isolation guarantee that it cannot verify.
7. Discovery can identify permitted capabilities, but discovery never grants trust or authority.
8. A newly discovered node is untrusted until explicitly authorized by policy.
9. Autonomous optimization may change placement and resource allocation only within declared limits and autonomy budgets.
10. Uncertain or unverifiable operations fail closed and preserve recoverable state.
11. Logical identity is independent from physical location.
12. Desired state is distinct from actual state; reconciliation is explicit.
13. Critical state is not committed without verification.
14. Immutable history is never silently rewritten.
15. Secrets are referenced, not embedded in ordinary manifests or state.
16. AI/learning may improve predictions and plans but cannot grant itself authority.
17. High-impact changes should support simulation or shadow evaluation before execution.
18. The carrier-file fragment mechanism is a storage backend, not the definition of the FS itself.
19. Explicit federation boundaries are required for cross-node discovery, trust, storage and execution.
20. Safe-stop preserves the last verified state when confidence, integrity, compatibility or policy is insufficient.
21. A Unified Computer is a logical computer, not a claim of physically coherent shared hardware across heterogeneous hosts.
22. Resource pooling preserves measurable differences in latency, bandwidth, capability, locality, reliability and failure domain.
23. Ordinary applications are never silently distributed when their runtime semantics do not support distribution.
24. Logical application, environment and session identity survives physical placement changes where the backend supports migration or checkpoint/restore.
25. A resource contributes to a Computer only after explicit admission and capability verification.
26. Hardware authority is explicit and adapter-mediated.
27. Wall-clock time is not the sole source of distributed ordering.
28. Reality observations are evidence, not assumptions.
29. Intent describes desired outcomes; implementation remains planner-controlled.
30. Higher schedulers constrain lower schedulers; lower schedulers cannot expand authority.
31. Recursive Computer composition preserves explicit identity, capability and trust boundaries.
32. The same logical object model must remain valid across deployment levels.
