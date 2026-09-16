# Agent Step 2026-09-16: Transport JSON Boundary Reconnaissance

## Question
Can duplicate JSON object member names enter the localhost Genesis control-plane request path and be silently collapsed before semantic request validation?

## Repository evidence
- `src/fs_overlay/transport.py` frames messages at 1 MiB and parses payloads with default `json.loads`, requiring only that the resulting value is a `dict`.
- `recv_message()` is consumed by `GenesisServer` and by the localhost transport test harness.
- `GenesisService` validates the resulting request schema, but that validation sees only the dictionary produced by the JSON parser. A duplicate member discarded by parsing cannot be detected there.
- The existing federation envelope parser already uses a duplicate-key rejecting `object_pairs_hook`, establishing a project precedent for security-sensitive wire decoding.

## External research
- RFC 8259 §4 says JSON object names should be unique and warns that duplicate-name behavior is unpredictable across implementations; many parsers retain only the last member.
- OWASP Developer Guide recommends not using duplicate JSON keys and generating fatal parse errors for duplicate keys because different parsers can apply different precedence.
- OWASP REST Security recommends validating untrusted input, enforcing type/format/size constraints, and rejecting unexpected content.
- External `secure-software-engineering` and OWASP `security-guidance` Agent Skills were inspected as advisory material. They reinforce strict validation at trust boundaries; neither overrides `fs-agent-core`.

## Decision
Treat duplicate JSON object member names as malformed localhost control-plane wire input. Reject them during transport decoding before semantic dispatch, using the same explicit duplicate-key rejection pattern already used by `FederationEnvelope`.

Do not change framing, the 1 MiB limit, loopback binding, authority semantics, or GenesisService request schema. This is a parser-integrity hardening only.

## Acceptance criteria
1. A normal unique-key object continues to round-trip unchanged.
2. A duplicate top-level member is rejected by `recv_message()` with a stable `ValueError`.
3. The rejection occurs before `GenesisService` receives a semantic request.
4. No duplicate-key acceptance path remains for the localhost control-plane decoder.
5. GitHub Actions full configured matrix is the authoritative validation evidence.

## Residual risk
This does not provide transport confidentiality, authenticated transport, trust-root management, or production key custody. Those remain separate V1 production blockers.
