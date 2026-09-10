# V1 Release Gate

This gate turns the current architecture into an evidence-based release checklist.

## Required evidence

- [ ] CI green on every supported platform/runtime combination.
- [ ] Independent federation conformance consumer passes.
- [ ] Independent admission conformance passes.
- [ ] Storage transaction crash/restart recovery passes.
- [ ] Durable admission ambiguity/recovery cases pass.
- [ ] Replay, stale, duplicate and revoked-key cases fail closed.
- [ ] Adapter qualification covers both positive and negative capability cases.
- [ ] Recovery graph rejects cycles and produces deterministic plans.
- [ ] Carrier changes enter quarantine rather than silent overwrite.
- [ ] Production confidentiality provider is an audited AEAD implementation.
- [ ] Key lifecycle documents active, retired and revoked states.
- [ ] Compatibility/version policy is documented.
- [ ] Minimal federation E2E lifecycle is reproducible from a clean environment.
- [ ] Two-node recovery scenario is reproducible.

## Release blockers

Any one of the following blocks release:

1. An adapter can obtain authority not represented by its declared capability contract.
2. Ambiguous durable state can be accepted as success without explicit evidence.
3. Replay protection can be bypassed.
4. Recovery can silently select an unapproved carrier.
5. Cryptography is described as confidential when it only provides integrity.
6. CI or conformance evidence is missing for a supported target.
7. A recovery or reconciliation operation is non-deterministic without an explicit reason.

## Evidence principle

A feature is not considered production-ready merely because its implementation exists. V1 requires executable evidence, independent conformance where practical, and explicit failure behavior.
