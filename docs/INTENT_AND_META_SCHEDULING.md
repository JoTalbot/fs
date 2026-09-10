# FS Intent and Meta-Scheduling

## Purpose

FS should allow the user to describe an outcome while the system determines a safe, compatible and resource-aware implementation.

The Intent Layer sits above Universal Runtime and scheduling.

## Intent pipeline

```text
USER INTENT
   -> REQUIREMENTS
   -> POLICY
   -> CAPABILITY MATCH
   -> RESOURCE PLAN
   -> ENVIRONMENT PLAN
   -> RUNTIME PLAN
   -> SIMULATION / SHADOW
   -> TRANSACTION
   -> VERIFICATION
```

## Intent object

An intent is a first-class logical object containing:

- stable identity;
- desired outcome;
- constraints;
- priority;
- deadline where applicable;
- required capabilities;
- resource budget;
- security requirements;
- recovery requirements;
- autonomy level;
- provenance;
- lifecycle state.

## Examples

```yaml
intent:
  run: application.exe
  interactive: true
  network: restricted
  data: private
  recovery: required
  mobility: allowed
```

The intent does not dictate whether the application uses a local process, VM or another compatible backend. The planner decides within policy.

## Meta-scheduler

FS uses hierarchical scheduling:

```text
World
  -> Computer
      -> Node
          -> Environment
              -> Runtime
                  -> Process / Task
```

The meta-scheduler allocates objectives and constraints downward. Lower schedulers return capacity, feasibility and execution results upward.

## Scheduling classes

FS should distinguish:

- interactive;
- latency-sensitive;
- batch;
- distributed;
- accelerator-bound;
- storage-heavy;
- background;
- recovery-critical.

Different classes use different optimization priorities.

## Feasibility before optimization

The scheduler must first determine whether a plan is valid:

```text
identity
policy
trust
compatibility
resource availability
security
failure-domain constraints
```

Only feasible candidates enter optimization.

## Multi-objective planning

A plan may optimize:

```text
performance
availability
durability
locality
energy
cost
migration effort
risk
```

Weights are policy-defined. Optimization never overrides hard constraints.

## Reservation and admission

Resources are reserved before high-impact execution where necessary. Reservations have owners, scopes, expiration and audit records.

A resource becomes usable by a Computer only after explicit admission and capability verification.

## Planning hierarchy

A plan contains nested decisions:

```text
Intent
  +-- Computer selection
      +-- Node selection
          +-- Environment selection
              +-- Runtime selection
                  +-- Process/task placement
                      +-- Device/resource bindings
```

Each decision can be explained and independently verified.

## Explainability

For every material scheduling decision FS should retain:

```text
selected target
requirements
constraints
candidates considered
rejected candidates + reasons
expected cost
risk/confidence
policy references
simulation result
```

## Safe failure

If no feasible plan exists, FS must not improvise authority. It should preserve the current verified state and return a structured failure explaining which requirement or constraint prevented execution.

## Recursive scheduling

A logical Computer may itself be scheduled as a resource by a higher Computer or World scheduler. This permits recursive composition while retaining explicit boundaries:

```text
World Scheduler
   -> Computer A Scheduler
       -> Computer B as resource
           -> Node Scheduler
```

## Architectural invariant

**Users specify intent; FS specifies implementation only within verified capability and policy boundaries.**
