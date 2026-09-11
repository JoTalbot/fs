from __future__ import annotations

from itertools import permutations

from fs_overlay.federation_protocol import FederationEnvelope, ReplayGuard


def _envelope(payload: dict[str, object]) -> FederationEnvelope:
    return FederationEnvelope(
        "node-a", "m1", "OBSERVE", 1, 1_000, payload,
        signature=b"signature",
    )


def test_canonical_bytes_are_independent_of_mapping_insertion_order() -> None:
    items = [
        ("alpha", {"z": 3, "a": [2, 1]}),
        ("beta", {"nested": {"b": 2, "a": 1}, "value": "x"}),
        ("gamma", {"unicode": "Привет", "number": 7}),
    ]
    digests = set()
    for order in permutations(items):
        payload = dict(order)
        digests.add(_envelope(payload).digest())
    assert len(digests) == 1


def test_canonical_digest_changes_when_signed_content_changes() -> None:
    base = _envelope({"value": 1})
    changed = _envelope({"value": 2})
    assert base.digest() != changed.digest()


def test_replay_guard_is_per_sender_and_sequence_monotonic() -> None:
    guard = ReplayGuard()
    assert guard.accept(FederationEnvelope("node-a", "a1", "OBSERVE", 1, 1_000, {}), now_ns=1_000)
    assert guard.accept(FederationEnvelope("node-b", "b1", "OBSERVE", 1, 1_000, {}), now_ns=1_000)
    assert guard.accept(FederationEnvelope("node-a", "a2", "OBSERVE", 2, 1_000, {}), now_ns=1_000)
    assert not guard.accept(FederationEnvelope("node-a", "a3", "OBSERVE", 2, 1_000, {}), now_ns=1_000)
    assert not guard.accept(FederationEnvelope("node-a", "a0", "OBSERVE", 0, 1_000, {}), now_ns=1_000)


def test_replay_guard_does_not_consume_rejected_envelopes() -> None:
    guard = ReplayGuard()
    stale = FederationEnvelope("node-a", "stale", "OBSERVE", 1, 0, {})
    assert not guard.accept(stale, now_ns=1_000, max_age_ns=100)
    fresh = FederationEnvelope("node-a", "fresh", "OBSERVE", 1, 1_000, {})
    assert guard.accept(fresh, now_ns=1_000, max_age_ns=100)
