# FS Unified Control Loop

## Purpose

The Unified Control Loop is the executable integration model connecting the architectural planes into one bounded feedback system.

```text
Intent
  -> Semantic Interpretation
  -> Requirements / Dependencies
  -> Knowledge + Reality Context
  -> Policy + Authority Validation
  -> Feasibility / Resource Admission
  -> Decision / Plan
  -> Simulation or Shadow Check
  -> Transaction
  -> Execution
  -> Observation
  -> Verification
  -> World State Update
  -> Provenance / Event History
  -> Knowledge + Learning Update
  -> Reconciliation
```

The loop is continuous, but every state-changing step remains explicit and attributable.

## Separation of Concerns

- Intent defines desired outcomes and constraints.
- Semantic Kernel defines meaning.
- Knowledge supplies evidence and estimates.
- Reality Engine observes actual conditions.
- Policy Compiler produces enforceable constraints.
- Authority Model determines whether an operation is permitted.
- Decision Engine ranks feasible alternatives.
- Meta Scheduler creates a resource-aware plan.
- Transaction Engine commits cross-space changes safely.
- Runtime executes through a selected backend.
- Verification establishes whether declared semantics were achieved.
- World State records the bounded logical state.
- Learning improves predictions without gaining authority.

## Closed-Loop Invariants

1. No execution without capability, authority, compatibility and resource checks.
2. No critical commit without verification.
3. Failed verification produces reconciliation/recovery rather than false success.
4. Observations may invalidate plans and trigger replanning.
5. Learning may alter estimates, never permissions.
6. Simulation branches cannot mutate live state directly.
7. Every material decision and state transition is provenance-linked.
8. Uncertainty can reduce autonomy but cannot silently relax requirements.

## Recursive Operation

The same loop may operate at application, environment, Computer and World levels. A higher-level loop delegates bounded intent to lower-level loops; lower levels cannot expand the authority or requirements inherited from above.

## System Character

This architecture turns FS from a collection of managers into a coherent control system: it continuously compares desired state with observed reality, computes a bounded correction, executes it transactionally, verifies the result and feeds the evidence back into the next cycle.
