from fs_overlay.federation_control import NodeIdentity, TrustEntry, TrustStore
from fs_overlay.federation_protocol import FederationEnvelope, FederationReceiver, ReplayGuard


def verifier(payload: bytes, signature: bytes, sender: str) -> bool:
    return signature == payload + sender.encode()


def signed(*, sequence: int = 1, issued_ns: int = 1_000_000_000, message_id: str = "m1", sender: str = "node-a", payload: dict[str, object] | None = None) -> FederationEnvelope:
    base = FederationEnvelope(sender, message_id, "OBSERVE", sequence, issued_ns, payload or {"object": "x"})
    return FederationEnvelope(sender, message_id, "OBSERVE", sequence, issued_ns, base.payload, base.unsigned_bytes() + sender.encode())


def test_changed_payload_sender_and_sequence_reject_with_unchanged_signature() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    original = signed()
    assert receiver.receive(FederationEnvelope("node-a", "m1", "OBSERVE", 1, 1_000_000_000, {"object": "changed"}, original.signature), now_ns=1_000_000_100) is None
    assert receiver.receive(FederationEnvelope("node-b", "m2", "OBSERVE", 1, 1_000_000_000, {"object": "x"}, original.signature), now_ns=1_000_000_100) is None
    assert receiver.receive(FederationEnvelope("node-a", "m3", "OBSERVE", 2, 1_000_000_000, {"object": "x"}, original.signature), now_ns=1_000_000_100) is None


def test_duplicate_id_and_sequence_rollback_reject() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    assert receiver.receive(signed(sequence=2, message_id="m1"), now_ns=1_000_000_100)
    assert receiver.receive(signed(sequence=3, message_id="m1"), now_ns=1_000_000_100) is None
    assert receiver.receive(signed(sequence=1, message_id="m2"), now_ns=1_000_000_100) is None


def test_stale_and_future_timestamps_reject() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    assert receiver.receive(signed(sequence=1, issued_ns=1), now_ns=301_000_000_000) is None
    assert receiver.receive(signed(sequence=2, issued_ns=1_000_000_200, message_id="future"), now_ns=1_000_000_100) is None


def test_missing_signature_rejects() -> None:
    receiver = FederationReceiver(verifier, ReplayGuard())
    message = signed()
    unsigned = FederationEnvelope(message.sender_node, "missing", message.message_type, message.sequence, message.issued_ns, message.payload, None)
    assert receiver.receive(unsigned, now_ns=1_000_000_100) is None


def test_unknown_and_revoked_key_reject() -> None:
    store = TrustStore([TrustEntry("node-a", "fp-a", True)])
    unknown = NodeIdentity("node-b", "fp-b", 1)
    assert not store.admit(unknown, now_ns=2)
    store.revoke("node-a")
    assert not store.admit(NodeIdentity("node-a", "fp-a", 1), now_ns=2)


def test_fingerprint_mismatch_reject() -> None:
    store = TrustStore([TrustEntry("node-a", "fp-a", True)])
    assert not store.admit(NodeIdentity("node-a", "fp-b", 1), now_ns=2)
