from fs_overlay.capability_negotiation import CapabilitySet, negotiate


def test_negotiation_intersects_features_deterministically() -> None:
    result = negotiate(CapabilitySet(1, frozenset({"storage", "audit"})), CapabilitySet(1, frozenset({"audit", "replication"})))
    assert result is not None
    assert result.features == ("audit",)


def test_negotiation_rejects_protocol_mismatch() -> None:
    assert negotiate(CapabilitySet(1, frozenset()), CapabilitySet(2, frozenset())) is None
