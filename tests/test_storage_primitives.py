"""Direct qualification of the local storage primitives.

``LocalStorageEngine`` is exercised end to end elsewhere; these tests pin the
primitive contracts themselves: manifest identity, deterministic chunking, the
integrity-only envelope, the erasure-coding interface, journal/inventory schema
validation and the Merkle DAG.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from fs_overlay.storage_engine import (
    DEFAULT_CHUNK_SIZE,
    FORMAT_VERSION,
    AppendJournal,
    DeterministicChunker,
    ErasureCoder,
    HMACIntegrityEnvelope,
    Inventory,
    JournalCorruption,
    LocalStorageEngine,
    Manifest,
    MerkleDAG,
)
from fs_overlay.storage_resilience import SnapshotStore

_OBJECT_ID = "a" * 64
_OTHER_ID = "b" * 64


def _canonical(raw: dict[str, object]) -> bytes:
    return json.dumps(raw, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _manifest(tmp_path: Path, payload: bytes = b"primitive payload") -> Manifest:
    return LocalStorageEngine(tmp_path, chunk_size=8).put(payload)


# --- Manifest ---------------------------------------------------------------


def test_manifest_round_trips_through_bytes(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)

    restored = Manifest.from_bytes(manifest.to_bytes())

    assert restored == manifest
    assert restored.identity() == manifest.object_id
    assert manifest.chunk_size == 8
    assert manifest.format_version == FORMAT_VERSION


def test_manifest_identity_excludes_object_id(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)

    assert "object_id" not in manifest.unsigned()
    assert manifest.identity() == manifest.object_id


def test_manifest_rejects_tampered_content(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    raw = json.loads(manifest.to_bytes())
    raw["size"] = manifest.size + 1

    with pytest.raises(ValueError, match="identity verification failed"):
        Manifest.from_bytes(_canonical(raw))


@pytest.mark.parametrize(
    "mutation",
    [
        {"size": -1},
        {"size": True},
        {"chunk_size": 0},
        {"chunks": "not-a-list"},
        {"chunks": ["zz"]},
        {"metadata": {"key": 1}},
        {"format_version": FORMAT_VERSION + 1},
        {"format_version": "1"},
    ],
)
def test_manifest_rejects_invalid_fields(tmp_path: Path, mutation: dict[str, object]) -> None:
    manifest = _manifest(tmp_path)
    raw = json.loads(manifest.to_bytes())
    raw.update(mutation)

    with pytest.raises(ValueError):
        Manifest.from_bytes(_canonical(raw))


def test_manifest_rejects_unknown_or_missing_fields(tmp_path: Path) -> None:
    raw = json.loads(_manifest(tmp_path).to_bytes())

    with pytest.raises(ValueError, match="schema is invalid"):
        Manifest.from_bytes(_canonical({**raw, "extra": 1}))

    raw.pop("size")
    with pytest.raises(ValueError, match="schema is invalid"):
        Manifest.from_bytes(_canonical(raw))


def test_manifest_rejects_non_json_and_duplicate_keys() -> None:
    with pytest.raises(ValueError, match="JSON is invalid"):
        Manifest.from_bytes(b"{not json")

    duplicated = _canonical({"object_id": _OBJECT_ID})[:-1] + b', "object_id": "' + _OBJECT_ID.encode() + b'"}'
    with pytest.raises(ValueError):
        Manifest.from_bytes(duplicated)


def test_manifest_rejects_non_object_payload() -> None:
    with pytest.raises(ValueError, match="schema is invalid"):
        Manifest.from_bytes(b"[1, 2, 3]")


# --- DeterministicChunker ---------------------------------------------------


def test_chunker_splits_deterministically_and_reassembles() -> None:
    data = b"x" * 25
    chunker = DeterministicChunker(chunk_size=8)

    chunks = list(chunker.split(data))

    assert [len(chunk) for chunk in chunks] == [8, 8, 8, 1]
    assert b"".join(chunks) == data
    assert list(DeterministicChunker(chunk_size=8).split(data)) == chunks


def test_chunker_default_chunk_size_is_one_mebibyte() -> None:
    assert DEFAULT_CHUNK_SIZE == 1024 * 1024
    assert DeterministicChunker().chunk_size == DEFAULT_CHUNK_SIZE


def test_chunker_streams_from_file_like_objects() -> None:
    data = b"streamed payload" * 4
    stream = io.BytesIO(data)

    assert b"".join(DeterministicChunker(chunk_size=16).split_stream(stream)) == data


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_chunker_rejects_non_positive_chunk_size(chunk_size: int) -> None:
    with pytest.raises(ValueError):
        DeterministicChunker(chunk_size=chunk_size)


# --- Integrity envelope -----------------------------------------------------


def test_integrity_envelope_round_trips_and_detects_tampering() -> None:
    envelope = HMACIntegrityEnvelope(b"0123456789abcdef")
    ciphertext = envelope.encrypt(b"payload", associated_data=b"object-id")

    assert envelope.decrypt(ciphertext, associated_data=b"object-id") == b"payload"

    tampered = bytearray(ciphertext)
    tampered[-1] ^= 0xFF
    with pytest.raises(ValueError, match="integrity verification failed"):
        envelope.decrypt(bytes(tampered), associated_data=b"object-id")

    with pytest.raises(ValueError, match="integrity verification failed"):
        envelope.decrypt(ciphertext, associated_data=b"other-object-id")


def test_integrity_envelope_is_documented_as_non_confidential() -> None:
    envelope = HMACIntegrityEnvelope(b"0123456789abcdef")

    assert envelope.name == "hmac-integrity-envelope"
    assert b"secret" in envelope.encrypt(b"secret")


def test_integrity_envelope_rejects_weak_keys_and_short_input() -> None:
    with pytest.raises(ValueError):
        HMACIntegrityEnvelope(b"short")

    envelope = HMACIntegrityEnvelope(b"0123456789abcdef")
    with pytest.raises(ValueError, match="invalid integrity envelope"):
        envelope.decrypt(b"too-short")


# --- Erasure-coding interface ----------------------------------------------


def test_erasure_coder_interface_declares_the_required_contract() -> None:
    """The repository ships the interface only; no production coder is claimed."""

    class StructuralCoder:
        name = "reference-parity"

        def encode(self, shards: list[bytes], *, parity_shards: int) -> list[bytes]:
            return [*shards, *[b"parity"] * parity_shards]

        def recover(self, shards: list[bytes | None], *, data_shards: int, parity_shards: int) -> list[bytes]:
            return [shard for shard in shards if shard is not None]

    coder: ErasureCoder = StructuralCoder()
    encoded = coder.encode([b"a", b"b"], parity_shards=1)

    assert len(encoded) == 3
    assert coder.recover([b"a", None, b"parity"], data_shards=2, parity_shards=1) == [b"a", b"parity"]


# --- Journal and inventory --------------------------------------------------


def _journal(tmp_path: Path) -> AppendJournal:
    return AppendJournal(tmp_path / "journal.log")


def _commit_payload(object_id: str = _OBJECT_ID, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"object_id": object_id, "size": 12, "manifest_path": object_id}
    payload.update(overrides)
    return payload


def test_inventory_publishes_plain_commits_and_applies_deletes(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    journal.append("commit", _commit_payload())
    journal.append("commit", _commit_payload(_OTHER_ID, size=4))
    journal.append("delete", {"object_id": _OBJECT_ID})

    inventory = Inventory(journal.path)

    assert set(inventory.records) == {_OTHER_ID}
    assert inventory.records[_OTHER_ID].size == 4


def test_inventory_publishes_staged_commits_only_on_transaction_commit(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    journal.append("transaction_begin", {"transaction_id": "tx-1"})
    journal.append("commit", _commit_payload(transaction_id="tx-1"))
    journal.append("transaction_commit", {"transaction_id": "tx-1", "object_ids": [_OBJECT_ID]})

    assert set(Inventory(journal.path).records) == {_OBJECT_ID}


def test_inventory_discards_aborted_transactions(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    journal.append("transaction_begin", {"transaction_id": "tx-1"})
    journal.append("commit", _commit_payload(transaction_id="tx-1"))
    journal.append("transaction_abort", {"transaction_id": "tx-1"})

    assert Inventory(journal.path).records == {}


def test_inventory_starts_empty_without_journal(tmp_path: Path) -> None:
    assert Inventory(tmp_path / "absent.log").records == {}


def test_inventory_rejects_unknown_operation(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    journal.append("rewrite-history", {"object_id": _OBJECT_ID})

    with pytest.raises(JournalCorruption, match="operation is invalid"):
        Inventory(journal.path)


@pytest.mark.parametrize(
    "operation,payload,match",
    [
        ("transaction_commit", {"transaction_id": "tx-1", "object_ids": [_OBJECT_ID]}, "out of order"),
        ("transaction_abort", {"transaction_id": "tx-1"}, "out of order"),
        ("transaction_begin", {"transaction_id": "tx-1", "extra": 1}, "schema is invalid"),
        ("transaction_commit", {"transaction_id": "tx-1"}, "schema is invalid"),
        ("delete", {"object_id": "short"}, "object_id is invalid"),
        ("delete", {}, "schema is invalid"),
    ],
)
def test_inventory_rejects_malformed_journal_records(
    tmp_path: Path, operation: str, payload: dict[str, object], match: str
) -> None:
    journal = _journal(tmp_path)
    journal.append(operation, payload)

    with pytest.raises(JournalCorruption, match=match):
        Inventory(journal.path)


def test_inventory_rejects_reopened_transaction_identifier(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    journal.append("transaction_begin", {"transaction_id": "tx-1"})
    journal.append("transaction_begin", {"transaction_id": "tx-1"})

    with pytest.raises(JournalCorruption, match="out of order"):
        Inventory(journal.path)


@pytest.mark.parametrize(
    "payload",
    [
        _commit_payload(manifest_path=_OTHER_ID),
        _commit_payload(size=-1),
        _commit_payload(size=True),
        _commit_payload(object_id="not-hex"),
        _commit_payload(unexpected=1),
        {"size": 1, "manifest_path": _OBJECT_ID},
        _commit_payload(transaction_id="tx-unknown"),
    ],
)
def test_inventory_rejects_invalid_commit_payloads(tmp_path: Path, payload: dict[str, object]) -> None:
    journal = _journal(tmp_path)
    journal.append("commit", payload)

    with pytest.raises(JournalCorruption):
        Inventory(journal.path)


# --- Merkle DAG -------------------------------------------------------------


def test_merkle_leaf_and_parent_are_deterministic() -> None:
    assert MerkleDAG.leaf(b"value") == MerkleDAG.leaf(b"value")
    assert MerkleDAG.leaf(b"value") != MerkleDAG.leaf(b"other")
    assert MerkleDAG.parent(["a", "b"]) == MerkleDAG.parent(["a", "b"])
    assert MerkleDAG.parent(["a", "b"]) != MerkleDAG.parent(["b", "a"])


def test_merkle_parent_requires_children() -> None:
    with pytest.raises(ValueError):
        MerkleDAG.parent([])


def test_merkle_root_is_order_sensitive_and_bottom_up() -> None:
    first = MerkleDAG.leaf(b"one")
    second = MerkleDAG.leaf(b"two")

    assert MerkleDAG.root([]) == MerkleDAG.leaf(b"")
    assert MerkleDAG.root([first]) == first
    assert MerkleDAG.root([first, second]) == MerkleDAG.parent([first, second])
    assert MerkleDAG.root([first, second]) != MerkleDAG.root([second, first])
    third = MerkleDAG.leaf(b"three")
    # An odd tail is wrapped in a single-child parent rather than promoted, so a
    # three-leaf root is parent(parent(a, b), parent(c)).
    assert MerkleDAG.root([first, second, third]) == MerkleDAG.parent(
        [MerkleDAG.parent([first, second]), MerkleDAG.parent([third])]
    )
    assert MerkleDAG.root([first, second, third]) != MerkleDAG.root([first, second])


def test_merkle_root_binds_snapshot_commitment(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=8)
    object_ids = [engine.put(payload).object_id for payload in (b"one", b"two", b"three")]
    snapshot = SnapshotStore(tmp_path / "snapshots").create(object_ids, generation=1)

    assert snapshot.merkle_root == MerkleDAG.root(sorted(object_ids))
    assert snapshot.merkle_root != MerkleDAG.root(sorted(object_ids)[:-1])
