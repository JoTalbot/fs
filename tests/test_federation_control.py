import json
from pathlib import Path

import pytest

import fs_overlay.federation_control as federation_control
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


def test_revocation_blocks_future_observation_and_existing_node_availability():
    identity = _identity()
    trust = TrustStore([TrustEntry(identity.node_id, identity.public_key_fingerprint, True)])
    directory = FederationDirectory(trust, _verifier)
    assert directory.observe(_ad(observed=1))
    assert len(directory.available()) == 1
    trust.revoke(identity.node_id)
    assert not directory.observe(_ad(observed=2))
    assert directory.available() == ()


def test_expired_trust_is_removed_from_available_view():
    identity = _identity("expired")
    trust = TrustStore([TrustEntry(identity.node_id, identity.public_key_fingerprint, True, expires_ns=10)])
    directory = FederationDirectory(trust, _verifier)
    assert directory.observe(_ad(identity.node_id, observed=1), now_ns=5)
    assert directory.available(now_ns=9)
    assert directory.available(now_ns=10) == ()


def test_reconciler_is_deterministic():
    identities = [_identity("a"), _identity("b"), _identity("c")]
    trust = TrustStore([TrustEntry(i.node_id, i.public_key_fingerprint, True) for i in identities])
    directory = FederationDirectory(trust, _verifier)
    for n in ("a", "b", "c"):
        assert directory.observe(_ad(n, 1))
    decisions = FederationReconciler(directory).plan_repairs("obj", present_on=("a",), desired_copies=3)
    assert [d.target_node for d in decisions] == ["b", "c"]


def test_reconciler_does_not_count_untrusted_present_replica():
    identities = [_identity("a"), _identity("b"), _identity("c")]
    trust = TrustStore([TrustEntry(i.node_id, i.public_key_fingerprint, True) for i in identities])
    directory = FederationDirectory(trust, _verifier)
    for n in ("a", "b", "c"):
        assert directory.observe(_ad(n, 1))
    decisions = FederationReconciler(directory).plan_repairs(
        "obj", present_on=("a", "untrusted"), desired_copies=2
    )
    assert [(d.source_node, d.target_node) for d in decisions] == [("a", "b")]


def test_reconciler_without_trusted_source_fails_closed():
    identity = _identity("a")
    directory = FederationDirectory(TrustStore(), _verifier)
    assert not directory.observe(_ad(identity.node_id))
    assert FederationReconciler(directory).plan_repairs(
        "obj", present_on=(identity.node_id, "untrusted"), desired_copies=2
    ) == ()


def test_reconciler_drops_disabled_source_immediately():
    identities = [_identity("a"), _identity("b"), _identity("c")]
    trust = TrustStore([TrustEntry(i.node_id, i.public_key_fingerprint, True) for i in identities])
    directory = FederationDirectory(trust, _verifier)
    for n in ("a", "b", "c"):
        assert directory.observe(_ad(n, 1))
    trust.revoke("a")
    assert FederationReconciler(directory).plan_repairs(
        "obj", present_on=("a",), desired_copies=2
    ) == ()


def test_reconciler_drops_expired_source_at_read_time():
    identities = [_identity("a"), _identity("b"), _identity("c")]
    trust = TrustStore([
        TrustEntry("a", "fp-a", True, expires_ns=10),
        TrustEntry("b", "fp-b", True),
        TrustEntry("c", "fp-c", True),
    ])
    directory = FederationDirectory(trust, _verifier)
    for n in ("a", "b", "c"):
        assert directory.observe(_ad(n, 1), now_ns=5)
    assert [d.target_node for d in FederationReconciler(directory).plan_repairs(
        "obj", present_on=("a",), desired_copies=2, now_ns=5
    )] == ["b"]
    assert FederationReconciler(directory).plan_repairs(
        "obj", present_on=("a",), desired_copies=2, now_ns=10
    ) == ()


def test_minimal_bootstrap_is_atomic(tmp_path):
    config = MinimalBootstrap(tmp_path / "node.json").initialize(root=tmp_path / "carrier", node_id="node-a")
    loaded = MinimalBootstrap(tmp_path / "node.json").load()
    assert loaded == config
    assert (tmp_path / "carrier").is_dir()


def test_bootstrap_directory_entry_is_synced_after_atomic_replace(tmp_path, monkeypatch):
    calls: list[Path] = []

    def record_directory_sync(directory: str | Path) -> None:
        calls.append(Path(directory))

    monkeypatch.setattr(federation_control, "_fsync_directory", record_directory_sync)
    config_path = tmp_path / "node.json"
    MinimalBootstrap(config_path).initialize(root=tmp_path / "carrier", node_id="node-a")
    assert calls == [tmp_path]


def test_bootstrap_load_rejects_coerced_types(tmp_path):
    config_path = tmp_path / "node.json"
    MinimalBootstrap(config_path).initialize(root=tmp_path / "carrier", node_id="node-a")
    data = json.loads(config_path.read_text())

    data["protocol_version"] = "1"
    config_path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="malformed bootstrap config"):
        MinimalBootstrap(config_path).load()

    data["protocol_version"] = 1
    data["initialized_ns"] = True
    config_path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="malformed bootstrap config"):
        MinimalBootstrap(config_path).load()


def test_bootstrap_load_rejects_unexpected_and_missing_fields(tmp_path):
    config_path = tmp_path / "node.json"
    MinimalBootstrap(config_path).initialize(root=tmp_path / "carrier", node_id="node-a")
    data = json.loads(config_path.read_text())

    data["unexpected"] = "value"
    config_path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="malformed bootstrap config"):
        MinimalBootstrap(config_path).load()

    data.pop("unexpected")
    data.pop("root")
    config_path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="malformed bootstrap config"):
        MinimalBootstrap(config_path).load()


def test_bootstrap_load_rejects_invalid_semantic_values(tmp_path):
    config_path = tmp_path / "node.json"
    MinimalBootstrap(config_path).initialize(root=tmp_path / "carrier", node_id="node-a")
    data = json.loads(config_path.read_text())

    data["node_id"] = ""
    config_path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="malformed bootstrap config"):
        MinimalBootstrap(config_path).load()

    data["node_id"] = "node-a"
    data["protocol_version"] = 0
    config_path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="malformed bootstrap config"):
        MinimalBootstrap(config_path).load()

    data["protocol_version"] = 1
    data["initialized_ns"] = -1
    config_path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="malformed bootstrap config"):
        MinimalBootstrap(config_path).load()
