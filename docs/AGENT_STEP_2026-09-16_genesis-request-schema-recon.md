# Agent Step Recon: Genesis control-plane request schema

## Question
Does the Genesis control-plane request boundary reject malformed or unexpected request fields before semantic operation dispatch, without changing the existing local-admission authority model?

## Sources
- Repository: `src/fs_overlay/genesis_service.py` at blob `025efc7f2e7621667ddbc000ac8143269a009368` before implementation.
- Repository: `src/fs_overlay/genesis_runtime.py` at blob `cf1b5c0b5b4d638b22d1a82fdd32dfed7177c091`.
- Repository: `src/fs_overlay/transport.py` at blob `cd1118f8e165d561d64264dfed2ba07e55856b5b`.
- Repository tests: `tests/test_genesis_service.py` at blob `44fbd2dfeed8add57a08f89937e4cf7c7eaeb6a6` before regression changes.
- Repository tests: `tests/test_genesis_server.py` at blob `cc7513aee9faf13f95ed63d0aba84a55087eb67a`.
- Canonical project skill: `.agents/skills/fs-agent-core/SKILL.md` at blob `c72b850c0975c101d61f130dad17b8a33429a97a`.
- Repository contract: `AGENTS.md` at blob `e27e98bb7f489741ac5ca5fa293c26b4cc3d28d2`.
- OWASP Input Validation Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- OWASP REST Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- External Agent Skill inspected: `magnus919/agent-skills/secure-software-engineering/SKILL.md`; used only as advisory guidance and not as an authority source.

## Important findings
1. `GenesisService.handle()` previously converted `request["operation"]` with `str(...)`. This allowed wrong-typed values to cross the semantic boundary as strings instead of being rejected as malformed input.
2. The existing operation surface is intentionally small: `ping`, `identity`, `capabilities`, and `execute`.
3. `execute` already required a non-empty list of strings for `argv` and was gated by explicit local `admitted` state. The request surface does not grant admission.
4. `transport.recv_message()` already requires a JSON object and enforces a 1 MiB framed-message limit, so transport-level framing is not the missing control.
5. OWASP guidance recommends server-side strong typing, allowlist validation, schema validation, and rejection of unexpected content. This supports strict semantic request validation at `GenesisService`, immediately before operation dispatch.
6. No new authentication, admission credential, command allowlist, or authority token is justified by this finding. Adding those would change the architecture rather than close the identified schema boundary.

## Decision
Define the exact request fields for each supported operation and reject wrong-typed `operation` values and unexpected fields before dispatch. Preserve existing operation names, response semantics for supported/unsupported operations, explicit local admission, and `argv` validation.

## Implementation
- `src/fs_overlay/genesis_service.py`: exact per-operation request field sets; strict string type for `operation`; unexpected-field rejection before operation handling.
- `tests/test_genesis_service.py`: regression coverage for wrong operation type, unexpected fields, and an unexpected execution-admission field.

## What remains unproven
- This change does not authenticate callers or establish production execution authority.
- It does not restrict the contents of an explicitly admitted `argv` beyond the existing non-empty string-list contract.
- It does not qualify the loopback transport as a production authenticated/encrypted channel.
- Full repository validation must be performed by GitHub Actions; no local test runner is available.
