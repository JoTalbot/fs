from __future__ import annotations

import hashlib
import json

import pytest

from fs_overlay.durable_admission import DurableKeyAdmission, DurableNodeAdmission


def fp(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def test_node_admission_restart_revoke_and_tamper(tmp_path):
    path = tmp_path / "nodes.jsonl"
    fingerprint = fp("node-key")
    store = DurableNodeAdmission(path)
    assert store.admit("node-1", fingerprint)
    assert store.is_admitted("node-1", fingerprint)
    assert DurableNodeAdmission(path).is_admitted("node-1", fingerprint)
    assert not store.admit("node-1", fp("different"))
    store.revoke("node-1")
    assert not store.admit("node-1", fingerprint)
    assert not DurableNodeAdmission(path).is_admitted("node-1", fingerprint)

    lines = path.read_text().splitlines()
    data = json.loads(lines[0])
    data["fingerprint"] = fp("tampered")
    path.write_text(json.dumps(data) + "\n" + "\n".join(lines[1:]) + "\n")
    with pytest.raises(ValueError):
        DurableNodeAdmission(path)


def test_node_replay_rejects_coerced_types_and_unknown_fields(tmp_path):
    path = tmp_path / "nodes.jsonl"
    store = DurableNodeAdmission(path)
    assert store.admit("node-1", fp("node-key"))
    data = json.loads(path.read_text().splitlines()[0])
    data["sequence"] = True
    path.write_text(json.dumps(data) + "\n")
    with pytest.raises(ValueError, match="malformed node admission record"):
        DurableNodeAdmission(path)

    store = DurableNodeAdmission(path.with_name("nodes-unknown.jsonl"))
    assert store.admit("node-1", fp("node-key"))
    data = json.loads(store.path.read_text().splitlines()[0])
    data["unexpected"] = "value"
    store.path.write_text(json.dumps(data) + "\n")
    with pytest.raises(ValueError, match="malformed node admission record"):
        DurableNodeAdmission(store.path)


def test_key_admission_lifecycle_and_restart(tmp_path):
    path = tmp_path / "keys.jsonl"
    fingerprint = fp("key-1")
    store = DurableKeyAdmission(path)
    assert store.admit_key("node-1", "key-1", fingerprint)
    assert store.is_key_admitted("node-1", "key-1", fingerprint)
    assert store.can_sign("node-1", "key-1")
    assert store.can_verify("node-1", "key-1")

    store.retire_key("node-1", "key-1")
    assert not store.admit_key("node-1", "key-1", fingerprint)
    restarted = DurableKeyAdmission(path)
    assert restarted.is_key_admitted("node-1", "key-1", fingerprint)
    assert not restarted.can_sign("node-1", "key-1")
    assert restarted.can_verify("node-1", "key-1")
    assert not restarted.admit_key("node-1", "key-1", fingerprint)

    restarted.revoke_key("node-1", "key-1")
    restarted = DurableKeyAdmission(path)
    assert not restarted.is_key_admitted("node-1", "key-1", fingerprint)
    assert not restarted.can_sign("node-1", "key-1")
    assert not restarted.can_verify("node-1", "key-1")
    assert not restarted.admit_key("node-1", "key-1", fingerprint)


def test_key_binding_rejects_fingerprint_change(tmp_path):
    store = DurableKeyAdmission(tmp_path / "keys.jsonl")
    assert store.admit_key("node-1", "key-1", fp("one"))
    assert not store.admit_key("node-1", "key-1", fp("two"))
    assert not store.is_key_admitted("node-2", "key-1", fp("one"))


def test_key_replay_rejects_coerced_types_and_unknown_fields(tmp_path):
    path = tmp_path / "keys.jsonl"
    store = DurableKeyAdmission(path)
    assert store.admit_key("node-1", "key-1", fp("key-1"))
    data = json.loads(path.read_text().splitlines()[0])
    data["sequence"] = "1"
    path.write_text(json.dumps(data) + "\n")
    with pytest.raises(ValueError, match="malformed key admission record"):
        DurableKeyAdmission(path)

    path = tmp_path / "keys-unknown.jsonl"
    store = DurableKeyAdmission(path)
    assert store.admit_key("node-1", "key-1", fp("key-1"))
    data = json.loads(path.read_text().splitlines()[0])
    data["unexpected"] = "value"
    path.write_text(json.dumps(data) + "\n")
    with pytest.raises(ValueError, match="malformed key admission record"):
        DurableKeyAdmission(path)
