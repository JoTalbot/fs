# Agent step: workspace transfer authority boundary

Date: 2026-09-15  
Repository: `JoTalbot/fs`  
Branch: `main`

## Result

The materializer admission boundary was hardened so it fails closed unless the
caller supplies an actual `TransferAuthority` instance issued through the
explicit authority API. Arbitrary objects, recovery decisions, audit events,
or other evidence records are not accepted as materialization authority.

The existing exact binding remains mandatory: ready transfer plan, materialize
scope, preserved source, matching snapshot/workspace identities, and a durable
PREPARED or MATERIALIZING journal transaction.

## Safety boundary

This is an authority-admission hardening step only. It does **not** make the
Python authority dataclass an authenticated security primitive. Before any real
host filesystem executor exists, authority issuance must be bound to an
authenticated principal/policy decision with provenance, revocation and audit
requirements. Recovery evidence and audit history remain evidence-only and do
not grant authority or advance journal state.

No host filesystem mutation was added.

## Validation

The regression suite now explicitly checks that a non-authority object is
rejected with a fail-closed permission error at the materializer boundary.
GitHub Actions is the authoritative validation environment for this session.

## Next

1. Keep authority issuance separate from capability detection and recovery evidence.
2. Inspect policy/control-plane contracts for the missing authenticated authority
   provenance, revocation and constraint-compilation boundary.
3. Only after that boundary is qualified, consider the narrowly scoped executor;
   host mutation remains disabled meanwhile.
