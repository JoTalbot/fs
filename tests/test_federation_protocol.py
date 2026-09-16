import concurrent.futures
import json

import pytest

from fs_overlay.federation_protocol import FederationEnvelope, FederationReceiver, ReplayGuard


def verifier(payload: bytes, signature: bytes, sender: str) -> bool:
    return signature == payload + sender.encode()


def signed(sequence: int = 1, issued_ns: int = 1_000_000_000, message_id: str = "m1") -> FederationEnvelope:
    base = FederationEnvelope("node-a", message_id, "OBSERVE", sequence, issued_ns, {"object": "x"})
    return FederationEnvelope(
        "node-a", message_id, "OBSERVE", sequence, issued_ns, {"object": "x"},
        base.unsigned_bytes() + b"node-a",
    )


def test_receiver_accepts_signed_message_and_rejects_duplicate() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    msg = signed()
    assert receiver.receive(msg, now_ns=1_000_000_100) == {"object": "x"}
    assert receiver.receive(msg, now_ns=1_000_000_100) is None


def test_receiver_rejects_non_increasing_sequence() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    assert receiver.receive(signed(2, message_id="m2"), now_ns=1_000_000_100)
    assert receiver.receive(signed(1, message_id="m3"), now_ns=1_000_000_100) is None


def test_receiver_rejects_stale_and_future_messages() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    assert receiver.receive(signed(1, issued_ns=1_000_000_000), now_ns=1_301_000_000_000) is None
    assert receiver.receive(signed(2, issued_ns=1_000_000_200, message_id="future"), now_ns=1_000_000_100) is None


def test_receiver_rejects_invalid_signature() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    tampered = FederationEnvelope("node-a", "bad", "OBSERVE", 1, 1_000_000_000, {}, b"bad")
    assert receiver.receive(tampered, now_ns=1_000_000_001) is None


def test_replay_guard_serializes_concurrent_duplicate_admission() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    envelope = signed()
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(
            lambda _: receiver.receive(envelope, now_ns=1_000_000_100),
            range(16),
        ))
    assert results.count({"object": "x"}) == 1
    assert results.count(None) == 15


def test_envelope_wire_round_trip_preserves_valid_state() -> None:
    envelope = signed()
    assert FederationEnvelope.from_bytes(envelope.to_bytes()) == envelope


def test_envelope_from_bytes_rejects_coercible_types() -> None:
    envelope = signed()
    payload = json.loads(envelope.to_bytes())

    payload["sequence"] = True
    with pytest.raises(ValueError, match="invalid federation envelope sequence"):
        FederationEnvelope.from_bytes(json.dumps(payload).encode())

    payload = json.loads(envelope.to_bytes())
    payload["sender_node"] = 123
    with pytest.raises(ValueError, match="invalid federation envelope sender_node"):
        FederationEnvelope.from_bytes(json.dumps(payload).encode())

    payload = json.loads(envelope.to_bytes())
    payload["payload"] = "not-an-object"
    with pytest.raises(ValueError, match="federation payload must be an object"):
        FederationEnvelope.from_bytes(json.dumps(payload).encode())


def test_envelope_from_bytes_rejects_unexpected_fields_and_invalid_signature() -> None:
    envelope = signed()
    payload = json.loads(envelope.to_bytes())
    payload["unexpected"] = "field"
    with pytest.raises(ValueError, match="federation envelope fields are invalid"):
        FederationEnvelope.from_bytes(json.dumps(payload).encode())

    payload = json.loads(envelope.to_bytes())
    payload["signature"] = 123
    with pytest.raises(ValueError, match="invalid federation envelope signature"):
        FederationEnvelope.from_bytes(json.dumps(payload).encode())


def test_envelope_from_bytes_rejects_duplicate_json_fields() -> None:
    envelope = signed()
    payload = envelope.to_bytes().decode()
    duplicate = payload.replace('"message_id":"m1"', '"message_id":"m1","message_id":"m2"', 1)
    with pytest.raises(ValueError, match="duplicate JSON fields"):
        FederationEnvelope.from_bytes(duplicate.encode())


def test_envelope_from_bytes_rejects_negative_numeric_fields() -> None:
    envelope = signed()
    payload = json.loads(envelope.to_bytes())
    payload["sequence"] = -1
    with pytest.raises(ValueError, match="invalid federation envelope sequence"):
        FederationEnvelope.from_bytes(json.dumps(payload).encode())

    payload = json.loads(envelope.to_bytes())
    payload["issued_ns"] = -1
    with pytest.raises(ValueError, match="invalid federation envelope issued_ns"):
        FederationEnvelope.from_bytes(json.dumps(payload).encode())
