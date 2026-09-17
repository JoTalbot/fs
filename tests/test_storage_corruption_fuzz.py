"""Deterministic mutation corpus for durable storage parsers.

This is intentionally bounded rather than a claim of exhaustive fuzz coverage.
It exercises malformed, truncated, duplicated, and type-mutated persistence
inputs without requiring a fuzzing service or nondeterministic test seed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from fs_overlay.storage_engine import AppendJournal, JournalCorruption, LocalStorageEngine, Manifest


def test_manifest_single_byte_mutations_fail_closed(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=8)
    manifest = engine.put(b"deterministic corruption corpus")
    encoded = (engine.store.manifests / manifest.object_id).read_bytes()

    positions = tuple(range(0, len(encoded), max(1, len(encoded) // 19)))
    for position in positions:
        mutated = bytearray(encoded)
        mutated[position] ^= 0x01
        with pytest.raises(ValueError):
            Manifest.from_bytes(bytes(mutated))


def test_manifest_truncation_corpus_fails_closed(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=8)
    manifest = engine.put(b"truncation corpus")
    encoded = (engine.store.manifests / manifest.object_id).read_bytes()

    for size in (0, 1, len(encoded) // 2, len(encoded) - 1):
        with pytest.raises(ValueError):
            Manifest.from_bytes(encoded[:size])


def test_manifest_schema_mutation_corpus_fails_closed(tmp_path: Path) -> None:
    engine = LocalStorageEngine(tmp_path, chunk_size=8)
    manifest = engine.put(b"schema mutation corpus")
    raw = json.loads((engine.store.manifests / manifest.object_id).read_text(encoding="utf-8"))

    mutations = [
        {**raw, "format_version": 0},
        {**raw, "size": "20"},
        {**raw, "chunks": "not-a-list"},
        {**raw, "chunk_size": True},
        {**raw, "metadata": ["not-an-object"]},
        {**raw, "extra": "unexpected"},
    ]
    for mutated in mutations:
        with pytest.raises(ValueError):
            Manifest.from_bytes(json.dumps(mutated, sort_keys=True).encode())


def _frame(body: bytes) -> bytes:
    return f"{len(body):016x}".encode() + body + b"\n"


def test_journal_corruption_corpus_rejects_complete_bad_frames(tmp_path: Path) -> None:
    path = tmp_path / "journal.log"
    journal = AppendJournal(path)
    journal.append("event", {"value": "valid"})

    cases = [
        _frame(b"{bad-json}"),
        _frame(b"{}"),
        _frame(b'[{"not":"an object"}]'),
    ]
    for corrupted in cases:
        path.write_bytes(corrupted)
        with pytest.raises(JournalCorruption):
            list(journal.replay())


def test_journal_tail_truncation_is_distinguished_from_corruption(tmp_path: Path) -> None:
    path = tmp_path / "journal.log"
    journal = AppendJournal(path)
    journal.append("first", {"value": 1})
    complete = path.read_bytes()
    path.write_bytes(complete + b"0000000000000010{")

    records = list(journal.replay())
    assert records == [{"version": 1, "operation": "first", "payload": {"value": 1}}]
