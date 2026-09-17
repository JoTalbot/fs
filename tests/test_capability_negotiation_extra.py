from fs_overlay.capability_negotiation import CapabilitySet, negotiate


def test_negotiation_rejects_zero_protocol_version() -> None:
    assert negotiate(CapabilitySet(0, frozenset()), CapabilitySet(0, frozenset())) is None


def test_negotiation_rejects_non_string_feature_names() -> None:
    capabilities = CapabilitySet(1, frozenset({"audit", 1}))
    assert negotiate(capabilities, CapabilitySet(1, frozenset({"audit"}))) is None
