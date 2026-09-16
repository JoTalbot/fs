# Genesis admission authority reconnaissance

Date: 2026-09-16

## Scope

Reviewed the local Genesis control path before any implementation change:

- `src/fs_overlay/genesis_service.py`
- `src/fs_overlay/genesis_runtime.py`
- `src/fs_overlay/genesis_server.py`
- `src/fs_overlay/transport.py`
- `src/fs_overlay/adapter.py`
- `src/fs_overlay/identity.py`
- `src/fs_overlay/production_adapters.py`
- `src/fs_overlay/durable_admission.py`
- `tests/test_genesis_service.py`
- `docs/AGENT_STEP_2026-09-15_authority-entrypoint-audit.md`

## Repository findings

`GenesisService.handle()` currently accepts an `admit` request when the supplied
`node_id` equals the service's local `NodeIdentity.node_id`. It then sets
`self.admitted = True`.

`GenesisServer` exposes `GenesisService.handle()` over the loopback transport.
Loopback addressing is a network-binding constraint, not an authorization
mechanism.

`build_local_service()` wires `GenesisService` directly to
`NativeProcessAdapter`. Once `self.admitted` is true, the executor callback
passes `admitted=True` to the adapter. The adapter then executes the supplied
argv without a shell.

The existing authority architecture is different: `production_adapters.py`
defines authoritative `NodeAdmission`/`KeyAdmission` interfaces and a composed
authenticated-principal validation path. The existing authority-entrypoint
audit documents `executor_preflight()` as the canonical new-execution admission
path for transfer mutation. No existing component establishes that a plain
loopback request carrying a node ID is an authenticated authority assertion.

## External research

OWASP authorization guidance distinguishes authentication from authorization,
requires server-side enforcement, and recommends least privilege and
deny-by-default behavior. OWASP OS command-injection guidance recommends
hardcoded/allowlisted commands and arguments when externally influenced input
reaches process execution.

## Decision

Do not invent a new network credential, trust token, command policy, or
production admission protocol. The concrete fail-closed fix is to remove the
network-callable `admit` transition from `GenesisService.handle()` and make
admission an explicit constructor/runtime configuration supplied by the local
caller. Remote Genesis requests therefore cannot turn a self-asserted node ID
into execution authority.

Keep `NodeIdentity` as identity metadata only. Do not treat matching a node ID
as authentication or authorization. Preserve the existing `NativeProcessAdapter`
explicit `admitted` guard.

## Expected regression coverage

Add tests proving:

1. a remote-style `admit` request is rejected and does not mutate admission
   state;
2. an explicitly locally admitted service can still execute its bounded argv;
3. an unadmitted service remains unable to execute;
4. identity/capability inspection and ping remain informational.

No production cryptographic or host-authority implementation is introduced by
this step.