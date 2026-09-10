# FS Constitution

This document defines architectural invariants for FS. It governs implementation choices even when a feature would be technically possible without following these rules.

## Core laws

1. **Logical identity is independent from physical location.** An object may move between carriers, volumes, nodes, or execution backends without changing its logical identity.
2. **Intent is distinct from reality.** Desired state and actual state are separate and reconciled explicitly.
3. **Physical storage is replaceable.** A carrier is an implementation detail, not the identity of the stored object.
4. **Execution backends are replaceable.** Native, container, sandbox, microVM, and VM backends are capabilities, not assumptions.
5. **Discovery never implies trust.** Capability discovery may describe a resource but never grants authority to use it.
6. **Authority never expands implicitly.** Adaptation, learning, or autonomous optimization cannot grant new permissions.
7. **Critical state is never committed without verification.** Integrity, policy, compatibility, and transaction invariants must pass before commit.
8. **Unexpected mutation is quarantined.** FS must not silently overwrite externally modified carriers or other critical state.
9. **There is no single indispensable metadata truth.** Critical state must be reconstructable from redundant metadata, immutable history, snapshots, or equivalent recovery records.
10. **History is append-oriented.** Immutable events, snapshots, packages, and audit records are never silently rewritten.
11. **Autonomy is policy-bounded.** Every automatic action has an authority boundary, resource budget, reason, verification result, and audit record.
12. **Uncertainty stops dangerous transitions.** If FS cannot establish a safe and verifiable result, it preserves recoverable state and enters a safe/degraded mode.
13. **Host functionality is preserved by default.** Stronger control requires an explicit supported isolation, virtualization, or system deployment mode.
14. **Secrets are referenced, not embedded.** Manifests and state contain secret references rather than raw credentials.
15. **Every critical object has provenance.** Identity, content lineage, generation, and relevant policy versions are traceable.
16. **Simulation precedes risky autonomy where practical.** High-impact plans should support dry-run, shadow, or what-if validation before execution.
17. **Failure is a normal state.** Recovery, degradation, migration, and repair are first-class lifecycle paths.
18. **Portability is a design property.** Platform-specific behavior belongs behind capability-aware adapters and versioned contracts.
19. **Emergent project changes require explicit approval.** A newly discovered idea, improvement, correction, architectural change, roadmap addition, or material implementation change that is not already authorized by the project contract must be proposed to the project owner before being applied.
20. **Approved changes are immediately persisted.** Once the project owner approves an emergent change, the decision and resulting project change should be recorded in the appropriate repository documentation, roadmap, specification, issue, or implementation without unnecessary delay, then development continues.
21. **Deferred and rejected proposals remain distinguishable.** When useful for future work and traceability, proposals that are not applied should be recorded as `DEFERRED` or `REJECTED` rather than silently disappearing.
22. **Approved implementation should not repeatedly block on reconfirmation.** Once a change is explicitly approved, its direct implementation steps and already-authorized consequences may proceed without asking for approval at every sub-step.

## Change proposal workflow

The normative workflow for emergent project ideas is:

```text
DISCOVER
   -> CLASSIFY
   -> ASSESS
   -> PROPOSE
   -> APPROVE / DEFER / REJECT

APPROVE
   -> PERSIST DECISION
   -> IMPLEMENT
   -> VERIFY
   -> RECORD RESULT
   -> CONTINUE DEVELOPMENT

DEFER
   -> RECORD BACKLOG ITEM
   -> CONTINUE DEVELOPMENT

REJECT
   -> RECORD DECISION WHEN TRACEABILITY IS USEFUL
   -> CONTINUE DEVELOPMENT
```

A proposal should normally state:

```text
idea
why_it_matters
scope
benefit
risks
cost_or_complexity
architectural_impact
recommended_action
```

The proposal workflow must not become a bottleneck for ordinary execution. Existing approved requirements, constitutional laws, accepted roadmap items, and direct implementation details do not require repeated approval.

## Four spaces

FS models four related but distinct spaces:

- **Data Space:** objects, files, volumes, shards, carriers, snapshots and content.
- **Compute Space:** processes, services, workloads, environments, containers and VMs.
- **Control Space:** policy, identity, planning, scheduling, reconciliation, recovery and safety.
- **Resource Space:** nodes, CPU, memory, storage, GPU, network, devices and other capabilities.

The control plane coordinates the other spaces without collapsing their responsibilities.

## Object state

Every managed object should be representable with at least:

```text
identity
kind
desired_state
actual_state
health
location
capabilities
dependencies
policy
history
```

The same state model should apply to files, shards, carriers, volumes, workloads, environments, nodes and resources.

## Autonomous action record

A critical automatic action must record:

```text
actor
policy_version
target
reason
before_state
intended_state
plan
resource_budget
risk/confidence
result
verification
rollback_reference
```

## Safety boundary

FS may become highly autonomous inside an explicitly authorized world, but it must not use that autonomy to perform covert persistence, hidden system-wide discovery, privilege escalation, credential harvesting, or silent modification of unrelated user/system data.
