from __future__ import annotations

import base64
import json

import pytest

from fs_overlay.capability_negotiation import CapabilitySet, negotiate
from fs_overlay.federation_protocol import FederationEnvelope


def test_envelope_canonicalization_is_independent_of_mapping_insertion_order() -> None:
    left = FederationEnvelope("node-a", "m1", "OBSERVE", 1, 1_000, {"z": 2, "nested": {"b": 2, "a": 1}, "a": 1})
    right = FederationEnvelope("node-a", "m1", "OBSERVE", 1, 1_000, {"a": 1, "nested": {"a": 1, "b": 2}, "z": 2})
    assert left.unsigned_bytes() == right.unsigned_bytes()
    assert left.digest() == right.digest()


def test_invalid_base64_signature_is_rejected_during_decode() -> None:
    data = json.dumps({"sender_node": "node-a", "message_id": "m1", "message_type": "OBSERVE", "sequence": 1, "issued_ns": 1_000, "payload": {}, "signature": "%%%not-base64%%%"}).encode()
    with pytest.raises((ValueError, base64.binascii.Error)):
        FederationEnvelope.from_bytes(data)


def test_capability_negotiation_is_deterministic_for_set_order() -> None:
    first = negotiate(CapabilitySet(1, frozenset({"z", "a", "m"})), CapabilitySet(1, frozenset({"m", "a", "q"})))
    second = negotiate(CapabilitySet(1, frozenset({"m", "z", "a"})), CapabilitySet(1, frozenset({"q", "a", "m"})))
    assert first == second
    assert first is not None
    assert first.features == ("a", "m")
