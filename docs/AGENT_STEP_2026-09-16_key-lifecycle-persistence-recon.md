# Agent Step: Key Lifecycle Persistence Reconnaissance

Date: 2026-09-16
Area: secure key lifecycle persistence boundary
Base: `a68fe13bc761ab42b7757d769440e6a7314d368d`

## Goal
Determine whether the repository currently contains a fail-open restart path that can resurrect retired or revoked key authority.

## Evidence reviewed
- `src/fs_overlay/key_lifecycle.py`: lifecycle records are constructor-supplied and maintained in memory; rotation, retirement, and revocation mutate the in-memory mapping only.
- `src/fs_overlay/production_adapters.py`: `ReferenceKeyLifecycleAdmission` is explicitly non-durable; node bindings and non-reactivation/revocation markers are process-local.
- `docs/KEY_STORAGE_PROVIDER_PLAN.md`: durable secure lifecycle state, restart/recovery semantics, authoritative fingerprints, and security review are explicitly requirements for a concrete production provider.
- `docs/FEDERATION_PROTOCOL.md`: authoritative admission and secure key lifecycle storage are deployment/provider responsibilities rather than guarantees of the reference implementation.

## Finding
No repository-level fail-open restart implementation was found. The absence of persistence in the reference lifecycle is an explicit provider boundary, not a hidden production fallback.

Adding persistence to the reference adapter would invent deployment-specific authority and could incorrectly turn an in-memory qualification fixture into a production authority. No such change is justified by the current repository evidence.

## Decision
- No code changes.
- Do not claim durable key revocation/rotation across restart for the reference implementation.
- Preserve the existing production blocker for concrete secure key storage/lifecycle evidence.

## Validation boundary
This was source/document reconnaissance only. No new implementation was introduced, so no new CI validation claim is made.

## Reusable learning
- In-memory lifecycle state must never be treated as durable revocation or rotation authority across restart.
- When a production property is explicitly delegated to an injected provider and no fail-open fallback exists, preserve the boundary instead of adding a generic persistence layer.
