from fs_overlay.conformance import validate_vectors
from fs_overlay.federation_protocol import FederationEnvelope


def test_versioned_conformance_vectors_pass() -> None:
    assert validate_vectors() == ("observe-v1",)


def test_envelope_round_trip_preserves_signature() -> None:
    envelope = FederationEnvelope("node", "id", "OBSERVE", 3, 100, {"x": "y"}, b"sig")
    restored = FederationEnvelope.from_bytes(envelope.to_bytes())
    assert restored == envelope
