import json

import pytest

from fs_overlay.trust_roots import DurableTrustRootStore


FP1 = "a" * 64
FP2 = "b" * 64


def test_durable_trust_root_store_survives_restart_and_rotates(tmp_path) -> None:
    path = tmp_path / "trust-roots.jsonl"
    store = DurableTrustRootStore(path)
    store.trust("issuer-1", FP1)
    assert store.issuer_fingerprint("issuer-1") == FP1

    restarted = DurableTrustRootStore(path)
    assert restarted.issuer_fingerprint("issuer-1") == FP1
    restarted.trust("issuer-1", FP2)
    assert restarted.issuer_fingerprint("issuer-1") == FP2
    assert DurableTrustRootStore(path).issuer_fingerprint("issuer-1") == FP2


def test_revoke_is_durable_and_fail_closed(tmp_path) -> None:
    path = tmp_path / "trust-roots.jsonl"
    store = DurableTrustRootStore(path)
    store.trust("issuer-1", FP1)
    store.revoke("issuer-1")
    assert store.issuer_fingerprint("issuer-1") is None
    assert DurableTrustRootStore(path).issuer_fingerprint("issuer-1") is None
    with pytest.raises(ValueError, match="issuer is not trusted"):
        store.revoke("issuer-1")


def test_replay_rejects_tampered_record(tmp_path) -> None:
    path = tmp_path / "trust-roots.jsonl"
    store = DurableTrustRootStore(path)
    store.trust("issuer-1", FP1)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["fingerprint"] = FP2
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="trust-root event digest mismatch"):
        DurableTrustRootStore(path)


def test_replay_rejects_non_boolean_revocation_flag(tmp_path) -> None:
    path = tmp_path / "trust-roots.jsonl"
    store = DurableTrustRootStore(path)
    store.trust("issuer-1", FP1)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["revoked"] = "false"
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed trust-root record"):
        DurableTrustRootStore(path)


def test_invalid_fingerprint_is_rejected_before_persistence(tmp_path) -> None:
    store = DurableTrustRootStore(tmp_path / "trust-roots.jsonl")
    with pytest.raises(ValueError, match="SHA-256 fingerprint"):
        store.trust("issuer-1", "not-a-fingerprint")
