# Agent Step — 2026-09-16 Revocation / Execution Race Recon

## Question

Does the current revocation check create a reproducible fail-open path in which a transfer authority can be revoked after preflight but before a future host filesystem mutation, with FS core nevertheless treating the preflight result as sufficient authority?

## Repository research

Reviewed:

- `src/fs_overlay/authority_revocation.py`
- `src/fs_overlay/workspace_transfer_materializer.py`
- `src/fs_overlay/executor_preflight.py`
- `src/fs_overlay/workspace_transfer_authority.py`
- relevant revocation and executor tests
- `AGENT_STATUS.md`
- `.agents/skills/fs-agent-core/SKILL.md`

Important findings:

- `AuthorityRevocationRegistry` serializes replay, revocation, and `is_revoked()` through the same cross-process file coordination boundary and refreshes durable state while holding the lock.
- `executor_preflight()` performs the live revocation check through `validate_authenticated_transfer_authority()` before returning executor inputs.
- The preflight result deliberately contains no host filesystem capability and is documented as non-host authority.
- `WorkspaceMaterializer` is only a protocol and the reference materializer performs no host mutation.
- The executor contract explicitly requires revalidation of authority, identity, transport, transaction, and recovery conditions immediately before mutation.

## External research

NIST SP 800-57 Part 1 Rev. 5 treats key management, trust anchors, and lifecycle controls as authoritative security infrastructure. OWASP Secrets Management guidance emphasizes revocation, rotation, lifecycle control, and least privilege. These sources support revalidation at the actual privileged operation rather than treating an earlier check as permanent authority.

## Skill discovery

Reviewed the repository `fs-agent-core` skill. External security-review and secure-software-engineering skills were also inspected as untrusted reference methodologies. Their relevant guidance is to identify trust boundaries, distinguish evidence from authority, and verify security properties at the actual execution boundary.

## Decision

No code change.

The apparent time-of-check/time-of-use gap is a requirement for the future authority-bearing executor, not a current fail-open defect in FS core. The current implementation deliberately does not mutate the host filesystem after preflight. Adding a lock that spans an unknown future executor, or adding a second revocation mechanism inside the core, would invent execution semantics that the architecture intentionally leaves to a separately qualified provider.

## What remains unproven

A future production executor must demonstrate that revocation is revalidated immediately before the first irreversible mutation and that its transaction/journal protocol prevents a revoked authority from being consumed after the final admission check. That evidence cannot be established by the current non-destructive reference implementation.

## Security boundary

This step does not claim that the system is immune to revocation races in a future deployment. It establishes only that the current repository does not expose such a race through an implemented host-mutating executor.
