# Agent step: policy-bound authority provenance

Date: 2026-09-15

## Change

The Phase 3 transfer authority boundary now has a dedicated policy-bound issuance path. `grant_policy_bound_transfer_authority()` requires a `PolicyAuthorization`, validates explicit approval and exact workspace/snapshot constraints, then issues the existing `TransferAuthority` contract.

The resulting authority carries immutable, non-secret provenance fields:

- `principal_id`
- `issuer_id`
- deterministic `policy_digest`
- deterministic `authority_id`

The identifiers are derived from canonical policy/authority inputs with SHA-256. They are correlation and integrity identifiers only, not authentication credentials or signatures.

## Safety boundary

- Capability detection does not grant authority.
- Policy approval is explicit and fail-closed.
- Workspace and snapshot bindings must match exactly.
- Source deletion remains prohibited.
- No filesystem mutation was added.
- The existing unbound `grant_transfer_authority()` contract remains available for compatibility; new control-plane integration should use the policy-bound path.
- Principal and issuer values remain claims supplied by an external authenticated control plane. This step does not authenticate them.

## Tests

Added `tests/test_workspace_transfer_policy_authority.py` covering successful provenance issuance, denied policy, workspace mismatch, snapshot mismatch, and deterministic correlation identifiers.

## Qualification

The previous authority boundary was green across the configured 18-job matrix. The policy-bound implementation/test commits are now pushed and require fresh GitHub Actions qualification. No local runner is available in this session.

## Remaining security gate

Before any host filesystem executor is enabled, add authenticated principal verification, explicit revocation semantics with durable fail-closed replay, and secure key/transport lifecycle. Do not treat the policy digest or authority ID as authentication.
