"""Qualification of filesystem publication durability boundaries."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

import fs_overlay.storage_engine as storage_engine
from fs_overlay.storage_engine import LocalStorageEngine, _fsync_directory


def test_object_publication_fsyncs_file_and_parent_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if os.name == "nt":
        pytest.skip("POSIX directory fsync is not exposed through the same API on Windows")
    fsync_fds: list[int] = []
    real_fsync = os.fsync

    def record_fsync(fd: int) -> None:
        fsync_fds.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(storage_engine.os, "fsync", record_fsync)
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    engine.put(b"directory durability")
    assert len(fsync_fds) >= 2


def test_manifest_publication_fsyncs_parent_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if os.name == "nt":
        pytest.skip("POSIX directory fsync is not exposed through the same API on Windows")
    calls: list[int] = []
    real_fsync = os.fsync

    def record_fsync(fd: int) -> None:
        calls.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(storage_engine.os, "fsync", record_fsync)
    engine = LocalStorageEngine(tmp_path, chunk_size=4)
    engine.put(b"manifest durability")
    assert len(calls) >= 2


def test_directory_fsync_helper_persists_directory_metadata(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("POSIX directory fsync is not exposed through the same API on Windows")
    directory = tmp_path / "new-dir"
    directory.mkdir()
    _fsync_directory(directory)
