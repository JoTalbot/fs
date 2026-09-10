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
