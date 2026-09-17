# Autonomous Development Master

This document is the top-level operating manual for continuous autonomous
development of `JoTalbot/fs`. It binds together the contract (`AGENTS.md`), the
task discipline (`docs/TASK-PROTOCOL.md`), the roadmap (`docs/ROADMAP.md`) and
the machine-readable state (`agent/state/current.yml`).

## Operating loop

```text
analyse state
  -> task graph
  -> parallel batch
  -> build / test
  -> repair
  -> integrate (commit, push, PR when CI evidence is needed)
  -> update state and roadmap
  -> next batch
```

The loop does not stop after one batch. It stops on a release gate, on a
recorded human blocker, or at the end of a session - and in the last case it
first writes the resume point.

## Entry protocol (every session)

1. Read `AGENT_STATUS.md`, then `agent/state/current.yml`.
2. Read `AGENTS.md`, `.agents/skills/fs-agent-core/SKILL.md` and
   `docs/TASK-PROTOCOL.md`.
3. Establish ground truth from the repository, not from the documents: current
   HEAD, branch, diff against `origin/main`, and a fresh test run.
4. Rebuild the local verification environment if it is missing.
5. Pick the next unblocked tasks from the task graph.

Documents may be stale. The repository, the test runner and the CI system are
authoritative.

## Exit protocol (every session)

1. Run the verification commands from `docs/TASK-PROTOCOL.md`.
2. Commit the work in coherent, atomic commits.
3. Push the session branch.
4. Update `agent/state/current.yml` (`head_commit`, task states,
   `resume_point`), `AGENT_STATUS.md` and `AGENT_LOG.md`.
5. Record durable learning in `.agents/skills/fs-agent-core/SKILL.md`.

A session that ends without a written resume point has wasted the next agent's
time, which is the most expensive resource in this project.

## Progress reporting

Progress is reported as counts against a named artifact, never as an invented
percentage:

```text
[ЭТАП]     what is being done
[ЗАЧЕМ]    why it matters
[ПРОГРЕСС] M1: 5/5 tasks, roadmap 116/353, tests 842 passed
[РЕЗУЛЬТАТ] what was actually produced and verified
[ДАЛЬШЕ]   the next concrete step
```

Where a percentage is impossible, use `done/total` for the milestone, the phase
or the release gate that is actually being worked on.

## Evidence discipline

`docs/V1_RELEASE_GATE.md` states the principle: existence is not readiness. The
loop therefore distinguishes, in this order of strength:

`planned -> available -> admitted -> executed -> observed -> verified -> committed`

A workflow that has never run is `available`. A test that ran locally is
`executed`. A CI matrix that ran on the exact commit is `observed`. Only
`observed` or `verified` evidence may close a gate item.

## Escalation

Escalate to a human blocker when:

- the connected integration lacks a required permission (record the HTTP status
  and endpoint that proved it);
- a decision is reserved to the project owner by `docs/CONSTITUTION.md`;
- external audit or deployment qualification is required;
- progress would require weakening a security invariant.

Everything else is diagnosed, repaired and re-run inside the loop.

## Anti-patterns

- Restarting a project that already has 85 modules and 96 test files.
- Reporting percentages that no artifact supports.
- Marking a roadmap item complete because a document mentions it.
- Declaring a gate closed because an implementation exists.
- Writing a long report instead of doing the next task.
- Asking a human to run a command the agent can run.
