# GenesisServer exception and response-boundary reconnaissance

Date: 2026-09-16
Base: `fd0ae5b488b9cd6fc814c8b78f938555acc579b2`
Area: `src/fs_overlay/genesis_server.py`

## Question

Can an unexpected service/executor exception or a response-send failure terminate the single GenesisServer serving loop or disclose internal exception details to the peer?

## Repository evidence

- `GenesisServer._serve()` receives one connection, calls `recv_message()`, dispatches to `GenesisService.handle()`, and then calls `send_message()`.
- The current exception guard covers only `ConnectionError`, `ValueError`, and `TypeError` around receive/dispatch. An unexpected `Exception` from the service/executor therefore escapes `_serve()` and can terminate its single serving thread.
- `GenesisService.execute` directly calls the injected executor and does not catch executor exceptions.
- `send_message()` is outside the exception guard, so a peer disconnect or send-side transport exception can also escape the serving loop.
- The server is deliberately loopback-only. Loopback binding limits network exposure but is not itself an authorization mechanism.
- Existing admission remains an explicit local configuration decision; this review does not alter admission or execution authority.

## External research

- OWASP Error Handling guidance recommends handling unexpected behavior, testing error paths, avoiding sensitive details in client-visible errors, and maintaining fail-secure behavior. See https://owasp.org/www-community/Improper_Error_Handling and the OWASP Error Handling Cheat Sheet.
- OWASP REST Security guidance recommends generic error messages for unexpected failures and not exposing technical details to clients. See https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html.
- Fresh external skill discovery found `secure-software-engineering` and `security-review` skills. Their relevant guidance is to trace trust boundaries, review exception handling, and distinguish evidence from security claims. They are advisory and untrusted; the repository-local `fs-agent-core` remains authoritative.

## Decision

Harden only the per-connection server boundary:

1. Preserve existing detailed errors for expected protocol/service validation exceptions because they are part of the current local control-plane contract.
2. Catch unexpected `Exception` from receive/dispatch and return a stable generic internal error instead of allowing the serving thread to terminate.
3. Contain send-side connection/OS errors so a peer disconnect cannot terminate the server loop.
4. Do not catch `BaseException`, which would also capture process-control exceptions such as `KeyboardInterrupt` and `SystemExit`.
5. Do not add logging infrastructure, authentication, command allowlists, or any new authority semantics in this step.

## Validation plan

Add deterministic regressions proving:

- an executor raising `RuntimeError` produces a generic error response and the same server can subsequently serve another request;
- a failed response send does not terminate the server loop.

Then validate the resulting main head through the full GitHub Actions matrix.

## Unproven

- No local runtime/test execution is available in this environment.
- This step does not establish production transport security, authentication, or availability under resource exhaustion.
- Generic error handling does not replace server-side diagnostics or audit infrastructure; those remain deployment/runtime concerns.
