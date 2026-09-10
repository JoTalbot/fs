---
name: linux-isolation-verification
description: Use when designing, implementing, probing, or verifying Linux namespaces, workspace isolation, network isolation, or related execution-boundary guarantees in FS.
---

# Linux Isolation Verification Skill

## Purpose

Build Linux execution boundaries from explicit capabilities and runtime evidence. Never equate the presence of an executable such as `unshare` with successful isolation.

## Required research

Before each substantive Linux isolation step:

1. Re-read the current FS implementation and tests.
2. Check current Linux kernel documentation and relevant man pages.
3. Search maintained upstream implementations for the exact mechanism.
4. Search current Agent Skills for a relevant isolation/security workflow.
5. Record the decision and remaining uncertainty in `AGENT_LOG.md`.

Useful primary references include Linux kernel namespace/resource-control documentation and current namespace tooling documentation.

## Evidence model

Keep these states separate:

```text
utility exists
    !=
backend is available
    !=
namespace creation succeeds
    !=
requested boundary is configured
    !=
requested boundary is observed
    !=
requested boundary is verified
```

A disposable probe should test exactly the operation whose capability is being claimed.

For FS's current namespace evidence contract:

- `namespace:mount` proves only the tested mount namespace operation;
- `namespace:pid` proves only the tested PID namespace operation;
- `namespace:net` proves only the tested network namespace operation.

Do not infer workspace binding, root filesystem replacement, cgroup enforcement, device isolation, or complete network denial from a generic namespace probe.

## User namespaces and privilege

Do not add privilege escalation to make a probe pass. User namespaces can change the security model and resource-control considerations, so any future use must be explicitly designed, documented, probed, and verified rather than silently introduced as a fallback.

## FS implementation pattern

```text
ExecutionBoundaryPlan
  ↓
Declared guarantees
  ↓
required_verification_checks()
  ↓
VerificationCheck
  ↓
Evidence provider / disposable probe
  ↓
VerificationResult
  ↓
Transaction commit gate
```

Unknown guarantees must not produce fake evidence requirements or silently pass verification. Unknown evidence providers return no evidence, which fails closed for required checks.

## Validation

Test both:

- successful evidence leading to commit;
- missing or failed evidence preventing commit.

Never report a namespace guarantee as verified because a plan object contains a guarantee string.

## Durable lessons

- Capability discovery is not runtime proof.
- Backend availability is not enforcement.
- Exact evidence scope must match the claimed guarantee.
- User namespace support must not be introduced as an unreviewed privilege workaround.
