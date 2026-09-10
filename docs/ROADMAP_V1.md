# FS V1 Roadmap — Production Readiness & Portable Federation

## Objective

Move FS from a validated local/control-plane substrate toward a production-oriented portable federation without weakening the existing fail-closed safety model.

## Phase 0 — Freeze the green baseline

- Preserve the currently passing CI matrix.
- Record the current protocol/conformance vectors as the V1 baseline.
- Treat every compatibility change as an explicit versioned change.

## Phase 1 — Contract audit

- Audit storage, state, policy, federation, runtime and HAL boundaries.
- Inventory TODO/FIXME/placeholder/NotImplemented paths.
- Identify every provider/adapter boundary and define required capabilities.
- Verify that no adapter silently gains authority outside its declared contract.

## Phase 2 — Failure and recovery qualification

- Add restart/crash recovery scenarios for durable admission and transactions.
- Exercise replay, duplicate delivery, stale envelopes and ambiguous durable state.
- Add property-based tests where deterministic invariants exist.
- Add bounded fuzzing for canonical serialization and admission inputs.
- Verify quarantine and safe-stop behavior under unexpected carrier/backend changes.

## Phase 3 — Portable adapter model

- Define a stable adapter capability schema.
- Add reference adapters with deliberately limited authority.
- Validate native, container and VM execution selection against declared policy.
- Add portability coverage for Linux, Windows, macOS and ARM-class environments.
- Keep platform-specific cryptography and secure-key storage behind explicit providers.

## Phase 4 — Minimal federation E2E

Validate one complete lifecycle:

bootstrap → identity → trust admission → capability negotiation → signed envelope → durable acceptance → reconciliation → authorized execution → verification → audit

Then validate:

normal restart → network loss → duplicate/replay → key rotation/revocation → recovery

## Phase 5 — Multi-node substrate

- Add two-node and three-node deterministic federation fixtures.
- Exercise failure-domain-aware placement and recovery.
- Keep object identity stable across nodes.
- Define convergence and conflict-resolution invariants.
- Measure recovery time and bounded resource usage.

## Phase 6 — Release gate

A V1 release should require:

- green supported-platform CI;
- independent conformance consumers passing;
- admission and recovery qualification passing;
- no unreviewed authority escalation in adapters;
- documented production cryptography providers;
- reproducible recovery tests;
- documented compatibility/version policy;
- end-to-end federation evidence.

## Explicit non-goals for V1

- silently scanning or modifying the host OS;
- arbitrary peer discovery;
- arbitrary socket/network authority;
- pretending development HMAC is encryption;
- shipping unaudited erasure coding as production functionality;
- boot/hypervisor integration before the lower control-plane contracts are proven.
