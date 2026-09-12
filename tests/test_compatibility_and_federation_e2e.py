from __future__ import annotations

import hashlib

from fs_overlay.capability_negotiation import CapabilitySet, negotiate
from fs_overlay.federation_control import (
    FederationDirectory,
    FederationReconciler,
    NodeAdvertisement,
    NodeIdentity,
    TrustEntry,
    TrustStore,
)
from fs_overlay.federation_protocol import FederationEnvelope, FederationReceiver
from fs_overlay.federation_state import DurableFederationState


class HmacFixture:
    """Deterministic test-only signer; production crypto remains a provider boundary."""

    def __init__(self, key: bytes):
        self.key = key

    def sign(self, payload: bytes) -> bytes:
        return hashlib.sha256(self.key + payload).digest()

    def verify(self, payload: bytes, signature: bytes, sender: str) -> bool:
        del sender
        return signature == self.sign(payload)


def test_protocol_version_mismatch_fails_closed() -> None:
    assert negotiate(CapabilitySet(1, frozenset({"a"})), CapabilitySet(2, frozenset({"a"}))) is None


def test_matching_version_negotiates_sorted_intersection() -> None:
    result = negotiate(
        CapabilitySet(1, frozenset({"z", "a", "shared"})),
        CapabilitySet(1, frozenset({"shared", "b", "a"})),
    )
    assert result is not None
    assert result.protocol_version == 1
    assert result.features == ("a", "shared")


def test_minimal_two_node_federation_round_trip_and_durable_admission(tmp_path) -> None:
    signer = HmacFixture(b"test-only-key")
    identity = NodeIdentity("node-a", "fp-a", 1, protocol_version=1)
    trust = TrustStore([TrustEntry("node-a", "fp-a", True)])
    directory = FederationDirectory(trust, verifier=signer.verify)

    unsigned_advertisement = NodeAdvertisement(identity, ("storage", "replication"), ("carrier-a",), 100)
    advertisement = NodeAdvertisement(
        identity,
        unsigned_advertisement.capabilities,
        unsigned_advertisement.carrier_ids,
        unsigned_advertisement.observed_ns,
        signer.sign(unsigned_advertisement.canonical_bytes()),
    )
    assert directory.observe(advertisement, now_ns=100) is True

    unsigned = FederationEnvelope(
        "node-a", "msg-1", "ADVERTISE", 1, 100,
        {"protocol_version": 1, "capabilities": ["storage", "replication"]},
    )
    envelope = FederationEnvelope(*unsigned.__match_args__[:-1], signature=signer.sign(unsigned.unsigned_bytes()))
    receiver = FederationReceiver(signer.verify)
    assert receiver.receive(envelope, now_ns=100) == {"protocol_version": 1, "capabilities": ["storage", "replication"]}

    state_a = DurableFederationState(tmp_path / "node-a.log")
    state_b = DurableFederationState(tmp_path / "node-b.log")
    assert state_a.accept(envelope) is True
    assert state_b.accept(envelope) is True
    assert DurableFederationState(tmp_path / "node-b.log").snapshot().last_sequence == {"node-a": 1}


def test_two_node_recovery_repairs_missing_replica_deterministically() -> None:
    signer = HmacFixture(b"test-only-key")
    identities = (
        NodeIdentity("node-a", "fp-a", 1, 1),
        NodeIdentity("node-b", "fp-b", 1, 1),
    )
    trust = TrustStore([TrustEntry("node-a", "fp-a", True), TrustEntry("node-b", "fp-b", True)])
    directory = FederationDirectory(trust)
    for index, identity in enumerate(identities, start=1):
        ad = NodeAdvertisement(identity, ("replication",), (f"carrier-{identity.node_id}",), index)
        signed = NodeAdvertisement(identity, ad.capabilities, ad.carrier_ids, ad.observed_ns,
                                    signer.sign(ad.canonical_bytes()))
        assert directory.observe(signed, now_ns=index)

    plan = FederationReconciler(directory).plan_repairs("object-1", present_on=("node-a",), desired_copies=2)
    assert plan == (plan[0],)
    assert plan[0].source_node == "node-a"
    assert plan[0].target_node == "node-b"
    assert plan[0].action == "REPLICATE"
