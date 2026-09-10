from fs_overlay.federation_control import (
    FederationDirectory,
    FederationReconciler,
    MinimalBootstrap,
    NodeAdvertisement,
    NodeIdentity,
    TrustEntry,
    TrustStore,
)


def _identity(node_id="n1"):
    return NodeIdentity(node_id, "fp-" + node_id, 1)


def _verifier(payload, signature, fingerprint):
    return signature == payload[:8] + fingerprint.encode()


def _ad(node_id="n1", observed=1):
    identity = _identity(node_id)
    ad = NodeAdvertisement(identity, ("storage",), observed_ns=observed)
    return NodeAdvertisement(identity, ad.capabilities, observed_ns=observed,
                             signature=ad.canonical_bytes()[:8] + identity.public_key_fingerprint.encode())


def test_unknown_or_unsigned_advertisement_is_rejected():
    directory = FederationDirectory(TrustStore(), _verifier)
    assert not directory.observe(_ad())


def test_trusted_signed_advertisement_and_monotonic_observation():
    identity = _identity()
    trust = TrustStore([TrustEntry(identity.node_id, identity.public_key_fingerprint, True)])
    directory = FederationDirectory(trust, _verifier)
    assert directory.observe(_ad(observed=2))
    assert not directory.observe(_ad(observed=2))
    assert not directory.observe(_ad(observed=1))


def test_revocation_blocks_future_observation():
    identity = _identity()
    trust = TrustStore([TrustEntry(identity.node_id, identity.public_key_fingerprint, True)])
    directory = FederationDirectory(trust, _verifier)
    assert directory.observe(_ad(observed=1))
    trust.revoke(identity.node_id)
    assert not directory.observe(_ad(observed=2))


def test_reconciler_is_deterministic():
    identities = [_identity("a"), _identity("b"), _identity("c")]
    trust = TrustStore([TrustEntry(i.node_id, i.public_key_fingerprint, True) for i in identities])
    directory = FederationDirectory(trust, _verifier)
    for n in ("a", "b", "c"):
        assert directory.observe(_ad(n, 1))
    decisions = FederationReconciler(directory).plan_repairs("obj", present_on=("a",), desired_copies=3)
    assert [d.target_node for d in decisions] == ["b", "c"]


def test_minimal_bootstrap_is_atomic(tmp_path):
    config = MinimalBootstrap(tmp_path / "node.json").initialize(root=tmp_path / "carrier", node_id="node-a")
    loaded = MinimalBootstrap(tmp_path / "node.json").load()
    assert loaded == config
    assert (tmp_path / "carrier").is_dir()
