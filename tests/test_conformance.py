import pytest

from fs_overlay.conformance import ConformanceVector, validate_vector, validate_vectors
from fs_overlay.federation_protocol import FederationEnvelope


def test_versioned_conformance_vectors_pass() -> None:
    assert validate_vectors() == ("observe-v1",)
    assert validate_vectors(strict=True) == ("observe-v1",)


def test_strict_conformance_rejects_mismatched_expected_digest() -> None:
    envelope = FederationEnvelope("node-a", "msg-1", "OBSERVE", 1, 1_000_000_000, {"object": "x"})
    vector = ConformanceVector("tampered-vector", envelope, "0" * 64)
    assert not validate_vector(vector)
    with pytest.raises(AssertionError, match="tampered-vector"):
        validate_vectors((vector,), strict=True)


def test_envelope_round_trip_preserves_signature() -> None:
    envelope = FederationEnvelope("node", "id", "OBSERVE", 3, 100, {"x": "y"}, b"sig")
    restored = FederationEnvelope.from_bytes(envelope.to_bytes())
    assert restored == envelope
