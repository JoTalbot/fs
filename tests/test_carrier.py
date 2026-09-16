from __future__ import annotations

import os

import pytest

from fs_overlay.carrier import LocalDirectoryCarrier


@pytest.mark.skipif(os.name == "nt", reason="directory fsync contract is not defined on Windows")
def test_put_propagates_directory_fsync_failure(tmp_path, monkeypatch) -> None:
    carrier = LocalDirectoryCarrier(tmp_path / "carrier")
    calls = 0
    real_fsync = os.fsync

    def fail_on_directory_fsync(fd: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected directory fsync failure")
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", fail_on_directory_fsync)

    with pytest.raises(OSError, match="injected directory fsync failure"):
        carrier.put("item", b"payload")
    assert carrier.root.joinpath("item").read_bytes() == b"payload"


@pytest.mark.skipif(os.name == "nt", reason="directory fsync contract is not defined on Windows")
def test_delete_propagates_directory_fsync_failure(tmp_path, monkeypatch) -> None:
    carrier = LocalDirectoryCarrier(tmp_path / "carrier")
    carrier.put("item", b"payload")

    def fail_fsync(fd: int) -> None:
        raise OSError("injected directory fsync failure")

    monkeypatch.setattr(os, "fsync", fail_fsync)

    with pytest.raises(OSError, match="injected directory fsync failure"):
        carrier.delete("item")
    assert not carrier.root.joinpath("item").exists()
