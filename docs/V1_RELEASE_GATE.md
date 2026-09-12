# V1 Release Gate

This gate turns the current architecture into an evidence-based release checklist.

## Required evidence

- [x] CI green on every supported platform/runtime combination (latest validated run #311: 9/9 jobs).
- [x] Independent federation conformance consumer passes.
- [x] Independent admission conformance passes.
- [x] Storage transaction crash/restart recovery passes.
- [x] Durable admission ambiguity/recovery cases pass.
- [x] Replay, stale, duplicate and revoked-key cases fail closed.
- [x] Adapter qualification covers both positive and negative capability cases.
- [x] Recovery graph rejects cycles and produces deterministic plans.
- [x] Carrier changes enter quarantine rather than silent overwrite.
- [ ] Production confidentiality provider is an audited AEAD implementation.
- [x] Key lifecycle documents active, retired and revoked states.
- [x] Compatibility/version policy is documented.
- [x] Minimal federation E2E lifecycle is reproducible from a clean environment.
- [x] Two-node recovery scenario is reproducible.

## Release blockers

Any one of the following blocks release:

1. An adapter can obtain authority not represented by its declared capability contract.
2. Ambiguous durable state can be accepted as success without explicit evidence.
3. Replay protection can be bypassed.
4. Recovery can silently select an unapproved carrier.
5. Cryptography is described as confidential when it only provides integrity.
6. CI or conformance evidence is missing for a supported target.
7. A recovery or reconciliation operation is non-deterministic without an explicit reason.

## Current blocker

The remaining V1 production-security blocker is concrete provider evidence. FS now has semantic AEAD provider qualification tests and explicit production requirements, but the repository does not falsely certify its non-cryptographic test double as an audited production implementation.

Production release additionally requires concrete secure key storage and authenticated/encrypted transport adapters with their own qualification evidence.

## Evidence principle

A feature is not considered production-ready merely because its implementation exists. V1 requires executable evidence, independent conformance where practical, and explicit failure behavior.
