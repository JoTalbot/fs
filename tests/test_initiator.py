from fs_overlay.federation_control import BootstrapConfig
from fs_overlay.initiator import InitiatorCapabilities, MinimalInitiator
from fs_overlay.federation_protocol import FederationEnvelope


class Keys:
    def active_key_id(self, node_id):
        return "k1"

    def public_key_fingerprint(self, key_id):
        return "fp1"


class Signer:
    def sign(self, payload, key_id):
        return b"signed:" + key_id.encode()

    def verify(self, payload, signature, key_id):
        return signature == b"signed:" + key_id.encode()


class Transport:
    def __init__(self):
        self.sent = []

    def send(self, peer_node, payload):
        self.sent.append((peer_node, payload))

    def receive(self):
        return None

    def close(self):
        pass


def test_initiator_sends_round_trippable_signed_envelope() -> None:
    transport = Transport()
    initiator = MinimalInitiator(
        BootstrapConfig("node-a", "/tmp/fs", 1, 1),
        key_provider=Keys(), signer=Signer(), transport=transport,
        capabilities=InitiatorCapabilities("linux", ("storage",)),
    )
    envelope = initiator.build_advertisement("m1", 100)
    initiator.send(envelope, "node-b")
    assert FederationEnvelope.from_bytes(transport.sent[0][1]) == envelope
    assert envelope.payload["key_id"] == "k1"
