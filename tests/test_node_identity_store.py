from __future__ import annotations

import json
import os

import pytest

from fs_overlay.identity import NodeIdentity
from fs_overlay.node_identity_store import LocalNodeIdentityStore


def _identity() -> NodeIdentity:
    return NodeIdentity.from_public_key("node-a", b"public-key")


def test_identity_store_round_trip(tmp_path):
    store = LocalNodeIdentityStore(tmp_path / "state" / "identity.json")
    identity = _identity()

    store.save(identity)

    assert store.load() == identity
    document = json.loads((tmp_path / "state" / "identity.json").read_text())
    assert document["schema_version"] == 1
    assert document["identity"]["node_id"] == "node-a"


def test_identity_store_missing_is_empty(tmp_path):
    assert LocalNodeIdentityStore(tmp_path / "identity.json").load() is None


def test_identity_store_rejects_malformed_json(tmp_path):
    path = tmp_path / "identity.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="encoding"):
        LocalNodeIdentityStore(path).load()


def test_identity_store_rejects_unknown_schema(tmp_path):
    path = tmp_path / "identity.json"
    path.write_text(json.dumps({"schema_version": 2}), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported"):
        LocalNodeIdentityStore(path).load()


def test_identity_store_rejects_invalid_identity(tmp_path):
    path = tmp_path / "identity.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "identity": {
                    "node_id": "node-a",
                    "public_key_fingerprint": "not-a-fingerprint",
                    "protocol_version": "1",
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="fingerprint"):
        LocalNodeIdentityStore(path).load()


def test_identity_store_rejects_boolean_schema_version(tmp_path):
    path = tmp_path / "identity.json"
    path.write_text(
        json.dumps({"schema_version": True, "identity": {}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="schema"):
        LocalNodeIdentityStore(path).load()


def test_identity_store_rejects_invalid_identity_on_save(tmp_path):
    identity = NodeIdentity("node-a", "x" * 64, "1")
    identity = NodeIdentity(identity.node_id, "not-hex" + "0" * 57, identity.protocol_version)

    with pytest.raises(ValueError, match="hexadecimal"):
        LocalNodeIdentityStore(tmp_path / "identity.json").save(identity)


def test_identity_store_save_uses_restrictive_mode_on_posix(tmp_path):
    if os.name == "nt":
        pytest.skip("POSIX mode bits are not authoritative on Windows")
    path = tmp_path / "identity.json"
    LocalNodeIdentityStore(path).save(_identity())
    assert path.stat().st_mode & 0o777 == 0o600
