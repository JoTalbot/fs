# Task Protocol

This protocol defines how autonomous work in `JoTalbot/fs` is decomposed,
claimed, verified and integrated. It operationalizes `AGENTS.md`; where the two
overlap, `AGENTS.md` and `docs/CONSTITUTION.md` win.

## Why this exists

Multiple agents work on this repository concurrently and none of them owns the
machine they run on. A task that exists only in one agent's session is not a
task; it is private context that will be lost. Every unit of work therefore has
a stable identifier, an owner, an explicit verification command and a recorded
result.

## Task identity

Task identifiers are `<milestone>-<sequence>`, for example `M1-03`.

- Milestones are defined in `docs/M0.md` (baseline), `docs/ROADMAP.md` (product
  phases) and `docs/V1_RELEASE_GATE.md` (release evidence).
- Identifiers are never reused. A task that is dropped is recorded as
  `dropped` with a reason.
- The live task graph is `agent/state/current.yml`. The narrative record is
  `AGENT_LOG.md`. The short human summary is `AGENT_STATUS.md`.

## Task states

| State | Meaning |
| --- | --- |
| `todo` | Defined, not started. |
| `in_progress` | Claimed by a named agent in this session. |
| `done` | Implemented **and** verified by a command that actually executed the changed code path. |
| `blocked` | A named blocker prevents progress; the blocker must be recorded with its exact observed evidence. |
| `dropped` | Abandoned with a reason; the reason stays in the log. |

`done` requires naming the function, module or command path that was executed.
"Compiles cleanly" and "the file was written" are not verification.

## Batch rules

Work proceeds in batches, and a batch is the unit of integration:

1. **Analysis** - read the current repository state, never a cached summary.
2. **Task graph** - select non-overlapping tasks; record claims.
3. **Parallel batch** - independent files may be worked concurrently; two tasks
   must never own the same file in the same batch.
4. **Build and test** - run the project's own runner over the changed paths.
5. **Repair** - diagnose real failures; never weaken an assertion to make a run
   green. A test that contradicts the intended behaviour is itself a finding.
6. **Integrate** - commit, push, and (where CI evidence is required) open a pull
   request so the real matrix executes.
7. **Update state** - `agent/state/current.yml`, `AGENT_STATUS.md`,
   `AGENT_LOG.md`, `docs/ROADMAP.md` when a claim changed.

A batch that cannot be verified is not committed as verified. If verification is
impossible in the environment, the commit and the log say so explicitly.

## Safety constraints inside a batch

- No change may widen an authority boundary; narrowing (fail-closed) is allowed.
- No secret material, credential or token enters repository state.
- No host mutation outside the working tree.
- Platform-specific isolation claims stay behind capability probes and are never
  reported stronger than the probe evidence.
- Destructive repository operations (force-push, history rewrite, branch
  deletion, merges into `main`) are not part of an autonomous batch.

## Verification commands

The canonical local loop, in a virtualenv because the host interpreter rejects
installs under PEP 668:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest
.venv/bin/python tools/roadmap_evidence.py
.venv/bin/python tools/independent_conformance_consumer.py
.venv/bin/python tools/independent_admission_conformance.py
```

Candidate production cryptography additionally runs
`.venv/bin/python -m pytest -m crypto_provider tests/test_production_crypto.py`
with the `crypto` extra installed.

## Claim format

A claim recorded in `agent/state/current.yml` or `AGENT_STATUS.md` states:
`agent_id`, `started_at`, `base_commit`, `area`, `claimed_files`, `goal`,
`status`, `next_step`. Do not take over a claim without checking Git history
first.

## Human blockers

Stop and record a blocker only when progress genuinely requires a human: a
permission the integration does not have, an external audit, a policy decision
reserved to the project owner by `docs/CONSTITUTION.md` law 19, or credentials
that must never be handled by an agent. Record the exact command and error
output that proved the blocker, then continue with unblocked tasks.
