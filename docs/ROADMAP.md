# FS Roadmap

## Phase 0 - foundation

- [x] architecture
- [x] FSOV envelope specification
- [x] explicit carrier safety policy
- [x] managed workspace concept
- [x] minimal runtime concept

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
- [ ] foreground runtime
- [ ] native service installers where appropriate
- [ ] local IPC control API
- [ ] structured JSON logs

## Phase 3 - managed workspaces

- [ ] workspace registration
- [ ] workspace health state
- [ ] migration/import workflow
- [ ] observed mode
- [ ] managed mode
- [ ] detach/export workflow
- [ ] adaptive carrier placement

## Phase 4 - resilience

- [ ] Reed-Solomon implementation or audited dependency
- [ ] metadata redundancy
- [ ] self-healing
- [ ] carrier quarantine
- [ ] failure-domain aware placement
- [ ] power-loss recovery tests
- [ ] corruption/fuzz tests

## Phase 5 - production

- [ ] security review
- [ ] threat model
- [ ] performance benchmarks
- [ ] Windows/Linux CI matrix
- [ ] signed releases
- [ ] upgrade/rollback mechanism
- [ ] disaster-recovery documentation

## Guiding rule

Every automatic action must be attributable, reversible where practical, constrained to an explicit workspace/root, and validated after the fact. Adaptability must increase compatibility, not silently expand authority.
