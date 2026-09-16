# Federation admission replay schema reconnaissance, 2026-09-16

## Question
Can malformed persisted federation admission state pass replay validation through Python's type relationships and influence the authoritative sender sequence high-water mark?

## Repository evidence
- `src/fs_overlay/federation_state.py` reconstructs `last_sequence` and `seen_message_ids` from hash-valid `EventLog` records whose event is `federation.accepted`.
- The replay validator required `sender_node` and `message_id` to be strings and required `sequence` with `isinstance(sequence, int)` plus a non-negative range check.
- Python's `bool` is a subclass of `int`, so persisted JSON `true` passed that check as integer `1`.
- The accepted value is stored in `last_sequence`, so a malformed durable event could alter subsequent admission decisions after restart. This is a state-integrity defect, not an authentication bypass by itself.
- The existing journal/event integrity checks still correctly authenticate the bytes represented by the event hash; the defect is that the semantically expected integer type was broader than the persisted schema contract.

## External research
- Python documentation states that `isinstance(obj, int)` is true for instances of `int` and subclasses, and `bool` is a subclass of `int`.
- OWASP Input Validation requires syntactic and semantic validation before processing untrusted structured data and recommends validation against expected data types.
- OWASP REST Security recommends validating input type, range and format and rejecting unexpected content.

## Skill discovery
- The repository-local `fs-agent-core` skill was reread. Its strict persisted-schema and fail-closed rules directly apply.
- No additional external skill was adopted. External security guidance is advisory and cannot override FS authority boundaries.

## Decision
Require the persisted federation admission `sequence` to have the exact Python `int` type using `type(sequence) is int`, while preserving the existing non-negative range check and all surrounding sender/message ordering checks.

Add a regression that writes a hash-valid `federation.accepted` event with JSON boolean `sequence: true` and proves restart fails closed before constructing a durable high-water mark from it.

## Consequence
A boolean cannot be interpreted as a numeric federation sequence during recovery. The change does not alter authentication, signature, trust, replay-ID, or multi-process coordination semantics.

## Validation target
GitHub Actions full 18-job matrix for the implementation/test head. No local test runner is available.
