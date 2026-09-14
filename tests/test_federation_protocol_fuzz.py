from __future__ import annotations

import base64
import json
import random

import pytest

from fs_overlay.federation_protocol import FederationEnvelope


def _payload(rng: random.Random, depth: int = 0):
    if depth >= 2:
        return rng.choice([None, True, False, rng.randint(-1000, 1000), f"v-{rng.randint(0, 9999)}"])
    kind = rng.randrange(5)
    if kind == 0:
        return None
    if kind == 1:
        return rng.randint(-1000, 1000)
    if kind == 2:
        return f"value-{rng.randint(0, 99999)}"
    if kind == 3:
        return [_payload(rng, depth + 1) for _ in range(rng.randrange(4))]
    return {f"k-{i}": _payload(rng, depth + 1) for i in range(rng.randrange(4))}


def _envelope(seed: int) -> FederationEnvelope:
    rng = random.Random(seed)
    payload = {f"field-{i}": _payload(rng) for i in range(rng.randrange(5))}
    return FederationEnvelope(
        sender_node=f"node-{rng.randrange(4)}",
        message_id=f"message-{seed}",
        message_type=rng.choice(["OBSERVE", "RECONCILE", "EXECUTE"]),
        sequence=seed,
        issued_ns=1_000_000_000 + seed,
        payload=payload,
        signature=bytes(rng.randrange(256) for _ in range(rng.randrange(33))),
    )


def test_bounded_randomized_envelope_round_trip_is_canonical() -> None:
    for seed in range(250):
        envelope = _envelope(seed)
        encoded = envelope.to_bytes()
        decoded = FederationEnvelope.from_bytes(encoded)
        assert decoded == envelope
        assert decoded.to_bytes() == encoded
        assert decoded.digest() == envelope.digest()


def test_payload_key_order_does_not_change_canonical_bytes() -> None:
    for seed in range(100):
        envelope = _envelope(seed)
        items = list(envelope.payload.items())
        random.Random(seed + 1000).shuffle(items)
        reordered = FederationEnvelope(
            envelope.sender_node,
            envelope.message_id,
            envelope.message_type,
            envelope.sequence,
            envelope.issued_ns,
            dict(items),
            envelope.signature,
        )
        assert reordered.to_bytes() == envelope.to_bytes()
        assert reordered.digest() == envelope.digest()


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"null",
        b"[]",
        b"{",
        b"not-json",
        b'{}',
        b'{"payload": []}',
        b'{"payload": {}, "signature": "%%%"}',
    ],
)
def test_malformed_envelopes_fail_closed(data: bytes) -> None:
    with pytest.raises((ValueError, KeyError, TypeError, json.JSONDecodeError)):
        FederationEnvelope.from_bytes(data)


def test_randomized_signature_text_is_strictly_base64_validated() -> None:
    envelope = _envelope(9001)
    value = json.loads(envelope.to_bytes())
    value["signature"] = base64.b64encode(b"valid").decode("ascii") + "!"
    with pytest.raises(ValueError):
        FederationEnvelope.from_bytes(json.dumps(value).encode())
