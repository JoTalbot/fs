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
- [ ] transaction engine implementation
- [ ] state/reconciliation engine implementation
- [ ] resource ownership/lease primitives
- [ ] causal event metadata
- [ ] universal object contract implementation
- [ ] provenance records
- [ ] dependency graph primitives
- [ ] knowledge record primitives
- [ ] decision record primitives
- [ ] world-state snapshot primitives
- [ ] unified control-loop primitives
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
- [ ] structured JSON logs
- [x] conservative local capability discovery
- [ ] capability negotiation
- [ ] versioned backend contracts
- [ ] hardware abstraction adapter
- [ ] hardware capability fingerprint
- [ ] platform time adapter
- [ ] monotonic/logical time adapter
- [ ] semantic ABI adapters
- [ ] semantic verification adapters
- [x] FS-IR backend lowering
- [ ] Genesis bootstrap executable
- [ ] local node identity store
- [x] platform capability adapter baseline

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
- [ ] provenance-aware recovery
- [ ] dependency-aware recovery ordering
- [ ] world-state recovery checkpoints
- [ ] transition-level compensation
- [ ] plan-level recovery

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
- [ ] semantic ABI compatibility validation

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
- [ ] capability graph engine
- [ ] transaction coordinator
- [ ] universal state machine engine
- [ ] world engine coordinator
- [ ] semantic kernel implementation
- [ ] universal object contract runtime
- [ ] intent-to-reality compiler
- [ ] knowledge plane
- [ ] decision engine
- [ ] learning/adaptation plane
- [ ] world-state coordinator
- [ ] unified control-loop coordinator
- [ ] executable-world coordinator
- [ ] computation planner
- [ ] Plan DAG compiler
- [ ] FS-IR compiler/lowering pipeline
- [ ] Genesis coordinator
- [ ] resource admission coordinator
- [ ] universal session coordinator

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
- [ ] distributed transaction semantics
- [ ] distributed causal ordering
- [ ] federated world model
- [ ] distributed authority/delegation
- [ ] federated provenance
- [ ] dependency-aware federation planning
- [ ] federated knowledge exchange
- [ ] federated decision provenance
- [x] distributed Plan DAG execution
- [ ] cross-node semantic verification
- [x] reciprocal resource participation
- [x] execution/presentation separation
- [x] cross-node application session placement
- [ ] federation privacy boundaries

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
- [ ] autonomous lease optimization
- [ ] capability-aware mobility optimization
- [ ] semantic plan optimization
- [ ] dependency-aware optimization
- [ ] intent-to-reality feedback optimization
- [ ] learned prediction models with provenance
- [ ] adaptation evaluation gates
- [ ] policy-compiled autonomy constraints

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
- [ ] transaction simulation
- [ ] world-level what-if execution
- [ ] authority simulation
- [ ] semantic execution simulation
- [ ] intent-to-reality simulation
- [ ] decision simulation
- [ ] policy compilation simulation
- [ ] learned-plan shadow evaluation
- [ ] complete control-loop simulation
- [ ] Plan DAG simulation
- [ ] state-transition replay
- [ ] FS-IR simulation
- [ ] Genesis federation simulation
- [ ] reciprocal two-node scenario
- [ ] application mobility simulation

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
- [ ] distributed transaction tests
- [ ] causal ordering tests
- [ ] lease/fencing tests
- [ ] world reconciliation tests
- [ ] semantic contract compatibility tests
- [ ] provenance integrity tests
- [ ] dependency graph correctness tests
- [ ] knowledge provenance tests
- [ ] decision reproducibility tests
- [ ] policy compiler conformance tests
- [ ] semantic ABI compatibility tests
- [ ] world-state replay tests
- [ ] control-loop invariant tests
- [ ] executable-world conformance tests
- [ ] computation model conformance tests
- [ ] Plan DAG correctness tests
- [ ] transition-machine invariant tests
- [ ] FS-IR compatibility tests
- [ ] Genesis bootstrap compatibility tests
- [ ] federation admission tests
- [ ] application mobility conformance tests

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
33. Resource ownership is explicit, bounded, auditable and revocable.
34. A lease is authority to allocate, not proof that the underlying resource remains healthy.
35. Causality must not be inferred solely from wall-clock timestamps.
36. Capability is evidence of possibility, not permission.
37. Cross-space state changes require explicit transaction and verification semantics.
38. Every managed object lifecycle is represented by explicit, validated state transitions.
39. FS World is an explicit trust and resource boundary, not a synonym for every machine visible on a network.
40. Recursive composition must preserve the same identity, capability, policy, state, time and recovery semantics at every level.
41. Semantic meaning is independent from implementation backend.
42. An FS object contract must remain stable enough to support migration, simulation and recursive composition.
43. Authority is evaluated independently from capability and intent.
44. Execution success requires observable verification of declared semantics.
45. Provenance is part of the identity and history of critical state, not an optional logging feature.
46. Dependencies are explicit graph relationships and must participate in planning and recovery.
47. Intent-to-reality compilation must never weaken requirements silently.
48. The FS World boundary is explicit, recursively composable and policy-governed.
49. Knowledge is evidence with provenance and confidence, not reality itself.
50. The Decision Engine recommends and explains; it does not execute or grant authority.
51. Learning may change predictions and preferences but never permissions, trust or authority.
52. Policies compile into explicit constraints; ambiguity and conflict do not silently broaden authority.
53. Semantic ABI compatibility is based on declared observable semantics, not platform labels alone.
54. World State is a bounded, versioned model and must remain distinguishable from live reality.
55. Simulation branches cannot affect live state without normal policy, authority and transaction promotion.
56. Learned behavior must remain attributable, versioned and reproducible.
57. The unified control loop is closed by observation and verification, not by assumption.
58. A World is executable only when intent, planning, execution, observation, verification and recovery are connected by explicit semantics.
59. Recursive control loops inherit constraints and cannot expand authority.
60. Every executable transition has explicit preconditions, effects and postconditions.
61. A plan is an intermediate artifact, not reality or authority.
62. Backend availability is not equivalent to enforcement capability.
63. Resource budgets require explicit ownership/delegation before enforcement.
64. A valid resource lease does not by itself prove that native limits are enforced.
