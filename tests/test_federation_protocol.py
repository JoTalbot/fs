import pytest

from fs_overlay.federation_protocol import FederationEnvelope, FederationReceiver, ReplayGuard


def verifier(payload: bytes, signature: bytes, fingerprint: str) -> bool:
    return signature == payload + fingerprint.encode()


def envelope(sequence: int = 1, issued_ns: int = 1_000_000_000, message_id: str = "m1") -> FederationEnvelope:
    unsigned = FederationEnvelope("node-a", message_id, "OBSERVE", sequence, issued_ns, {"object": "x"})
    return FederationEnvelope(
        unsigned.sender_node,
        unsigned.message_id,
        unsigned.message_type,
        unsigned.sequence,
        unsigned.issued_ns,
        unsigned.payload,
        unsigned=unsigned.unsigned_bytes() if False else None,
    )


def signed(sequence: int = 1, issued_ns: int = 1_000_000_000, message_id: str = "m1") -> FederationEnvelope:
    base = FederationEnvelope("node-a", message_id, "OBSERVE", sequence, issued_ns, {"object": "x"})
    return FederationEnvelope("node-a", message_id, "OBSERVE", sequence, issued_ns, {"object": "x"}, base.unsigned_bytes() + b"fp")


def test_receiver_accepts_signed_message_and_rejects_duplicate() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    msg = signed()
    assert receiver.receive(msg, now_ns=1_000_000_100) == {"object": "x"}
    with pytest.raises(ValueError, match="duplicate"):
        receiver.receive(msg, now_ns=1_000_000_100)


def test_receiver_rejects_non_increasing_sequence() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    assert receiver.receive(signed(2, message_id="m2"), now_ns=1_000_000_100)
    with pytest.raises(ValueError, match="sequence"):
        receiver.receive(signed(1, message_id="m3"), now_ns=1_000_000_100)


def test_receiver_rejects_stale_and_future_messages() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard(max_age_ns=100, future_skew_ns=10))
    with pytest.raises(ValueError, match="stale"):
        receiver.receive(signed(1, issued_ns=1_000_000_000), now_ns=1_000_000_101)
    with pytest.raises(ValueError, match="future"):
        receiver.receive(signed(2, issued_ns=1_000_000_200, message_id="future"), now_ns=1_000_000_100)


def test_receiver_rejects_invalid_signature() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    base = FederationEnvelope("node-a", "bad", "OBSERVE", 1, 1_000_000_000, {})
    tampered = FederationEnvelope("node-a", "bad", "OBSERVE", 1, 1_000_000_000, {}, b"bad")
    assert base.signature is None
    with pytest.raises(ValueError, match="signature"):
        receiver.receive(tampered, now_ns=1_000_000_001)
