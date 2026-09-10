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

## Phase 1 - local reference engine

- [ ] manifest model
- [ ] deterministic chunker
- [ ] authenticated encryption interface
- [ ] erasure-coding interface
- [ ] carrier adapter interface
- [ ] atomic append protocol
- [ ] inventory database with redundant recovery records
- [ ] audit command
- [ ] recovery command

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

## Phase 5 - resilience

- [ ] Reed-Solomon implementation or audited dependency
- [ ] metadata redundancy
- [ ] self-healing
- [ ] carrier quarantine
- [ ] failure-domain aware placement
- [ ] power-loss recovery tests
- [ ] corruption/fuzz tests
- [ ] workspace disaster recovery

## Phase 6 - isolation platform

- [ ] container backend where available
- [ ] sandbox backend where available
- [ ] microVM backend research
- [ ] VM backend research
- [ ] virtual disk stored in FS container
- [ ] guest lifecycle manager
- [ ] host-independent workspace import/export

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

## Phase 8 - production

- [ ] security review
- [ ] threat model
- [ ] performance benchmarks
- [ ] Windows/Linux/macOS CI matrix
- [ ] signed releases
- [ ] upgrade/rollback mechanism
- [ ] disaster-recovery documentation
- [ ] compatibility test suite

## Guiding rules

1. FS must preserve host functionality unless the operator explicitly selects an isolated/system deployment.
2. Every automatic action must be attributable, reversible where practical, constrained to an explicit workspace/root, and validated after the fact.
3. Adaptability increases compatibility; it never silently expands authority.
4. The resident daemon remains minimal. Heavy capabilities are workers/modules.
5. Stronger-than-host isolation requires explicit platform mechanisms such as containers, sandboxes, microVMs or VMs.
6. FS must never claim a recovery or isolation guarantee that it cannot verify.
