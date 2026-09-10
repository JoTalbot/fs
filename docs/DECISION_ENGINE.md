# FS Decision Engine

## Purpose

The Decision Engine converts verified context into ranked, explainable options. It does not execute actions and cannot create authority.

## Pipeline

`Context -> Constraints -> Candidate Options -> Feasibility -> Risk -> Cost -> Confidence -> Ranking -> Decision Record`

Feasibility precedes optimization. An impossible or policy-invalid option is not made acceptable by a high score.

## Inputs

- Reality observations
- Knowledge with provenance
- Intent and requirements
- Capability Graph
- Dependency Graph
- Resource Ownership and leases
- Policy and authority constraints
- Historical execution evidence
- Simulation/shadow results

## Outputs

Each decision record contains:

- decision id
- target and scope
- candidate plans
- rejected candidates and reasons
- selected plan
- constraints considered
- confidence and uncertainty
- expected impact
- provenance
- policy/authority references

## Safety Boundary

The engine recommends. Authority enforcement, resource admission, transactions and runtime execution remain separate stages.

No decision may expand permissions, bypass policy or convert uncertainty into authorization.
