from fs_overlay.federation_control import BootstrapConfig, NodeIdentity, TrustEntry, TrustStore
from fs_overlay.federation_protocol import FederationEnvelope, FederationReceiver
from fs_overlay.federation_state import DurableFederationState
from fs_overlay.initiator import InitiatorCapabilities, MinimalInitiator
from fs_overlay.reference_adapters import HmacReferenceSigner, MemoryKeyProvider


class NullTransport:
    def send(self, peer_node: str, payload: bytes) -> None:
        return None


def test_local_federation_admission_persists_replay_state(tmp_path) -> None:
    key_id = "node-a"
    key = b"local-reference-key"
    provider = MemoryKeyProvider({key_id: key}, {key_id: key_id})
    signer = HmacReferenceSigner({key_id: key})
    initiator = MinimalInitiator(
        config=BootstrapConfig(key_id, str(tmp_path), protocol_version=1, initialized_ns=1_000_000_000),
        key_provider=provider,
        signer=signer,
        transport=NullTransport(),
        capabilities=InitiatorCapabilities("test", ("storage",)),
    )

    now_ns = 2_000_000_000
    envelope = initiator.build_advertisement("m1", now_ns, capabilities=("compute",))
    identity = NodeIdentity(
        key_id,
        provider.public_key_fingerprint(key_id),
        created_ns=1_000_000_000,
        protocol_version=1,
    )
    trust = TrustStore((TrustEntry(key_id, identity.public_key_fingerprint, True),))
    assert trust.admit(identity, now_ns=now_ns)

    receiver = FederationReceiver(signer.verify)
    assert receiver.receive(envelope, now_ns=now_ns + 1) == envelope.payload

    state_path = tmp_path / "federation-events.jsonl"
    state = DurableFederationState(state_path)
    assert state.accept(envelope)
    assert not state.accept(envelope)

    restarted = DurableFederationState(state_path)
    assert restarted.snapshot().last_sequence == {key_id: 1}
    assert "m1" in restarted.snapshot().seen_message_ids


def test_local_federation_rejects_tamper_and_revocation(tmp_path) -> None:
    key_id = "node-a"
    key = b"local-reference-key"
    provider = MemoryKeyProvider({key_id: key}, {key_id: key_id})
    signer = HmacReferenceSigner({key_id: key})
    config = BootstrapConfig(key_id, str(tmp_path), protocol_version=1, initialized_ns=1_000_000_000)
    initiator = MinimalInitiator(
        config=config,
        key_provider=provider,
        signer=signer,
        transport=NullTransport(),
        capabilities=InitiatorCapabilities("test"),
    )
    envelope = initiator.build_advertisement("m2", 2_000_000_000)
    receiver = FederationReceiver(signer.verify)

    tampered = FederationEnvelope(
        envelope.sender_node,
        envelope.message_id,
        envelope.message_type,
        envelope.sequence,
        envelope.issued_ns,
        {"platform": "tampered"},
        envelope.signature,
    )
    assert receiver.receive(tampered, now_ns=2_000_000_001) is None

    fingerprint = provider.public_key_fingerprint(key_id)
    trust = TrustStore((TrustEntry(key_id, fingerprint, True),))
    identity = NodeIdentity(key_id, fingerprint, created_ns=1_000_000_000)
    assert trust.admit(identity, now_ns=2_000_000_000)
    trust.revoke(key_id, "test revocation")
    assert not trust.admit(identity, now_ns=2_000_000_001)
