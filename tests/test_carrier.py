from __future__ import annotations

import os

import pytest

from fs_overlay.carrier import LocalDirectoryCarrier


@pytest.mark.skipif(os.name == "nt", reason="race-resistant carrier is POSIX-only")
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


@pytest.mark.skipif(os.name == "nt", reason="race-resistant carrier is POSIX-only")
def test_delete_propagates_directory_fsync_failure(tmp_path, monkeypatch) -> None:
    carrier = LocalDirectoryCarrier(tmp_path / "carrier")
    carrier.put("item", b"payload")

    def fail_fsync(fd: int) -> None:
        raise OSError("injected directory fsync failure")

    monkeypatch.setattr(os, "fsync", fail_fsync)

    with pytest.raises(OSError, match="injected directory fsync failure"):
        carrier.delete("item")
    assert not carrier.root.joinpath("item").exists()


@pytest.mark.skipif(os.name == "nt", reason="race-resistant carrier is POSIX-only")
def test_rejects_existing_intermediate_symlink(tmp_path) -> None:
    carrier = LocalDirectoryCarrier(tmp_path / "carrier")
    outside = tmp_path / "outside"
    outside.mkdir()
    carrier.root.joinpath("nested").symlink_to(outside, target_is_directory=True)

    with pytest.raises(OSError):
        carrier.put("nested/item", b"payload")
    with pytest.raises(OSError):
        carrier.get("nested/item")
    with pytest.raises(OSError):
        carrier.delete("nested/item")

    assert not outside.joinpath("item").exists()


@pytest.mark.skipif(os.name == "nt", reason="race-resistant carrier is POSIX-only")
def test_rejects_leaf_symlink_without_following_target(tmp_path) -> None:
    carrier = LocalDirectoryCarrier(tmp_path / "carrier")
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"outside")
    carrier.root.joinpath("item").symlink_to(outside)

    with pytest.raises(OSError):
        carrier.get("item")
    assert carrier.contains("item") is False

    carrier.put("item", b"inside")
    assert outside.read_bytes() == b"outside"
    assert carrier.get("item") == b"inside"


@pytest.mark.skipif(os.name == "nt", reason="race-resistant carrier is POSIX-only")
@pytest.mark.parametrize("relative_name", ["", ".", "./item", "nested/../item", "../item", "/absolute"])
def test_rejects_non_canonical_relative_names(tmp_path, relative_name: str) -> None:
    carrier = LocalDirectoryCarrier(tmp_path / "carrier")
    with pytest.raises(ValueError, match="relative path|components"):
        carrier.contains(relative_name)


@pytest.mark.skipif(os.name == "nt", reason="race-resistant carrier is POSIX-only")
def test_root_directory_descriptor_survives_root_path_replacement(tmp_path) -> None:
    root = tmp_path / "carrier"
    carrier = LocalDirectoryCarrier(root)
    original = tmp_path / "original"
    root.rename(original)
    outside = tmp_path / "outside"
    outside.mkdir()
    root.symlink_to(outside, target_is_directory=True)

    carrier.put("item", b"payload")

    assert original.joinpath("item").read_bytes() == b"payload"
    assert not outside.joinpath("item").exists()


def test_windows_fails_closed_without_native_reparse_point_implementation(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(os, "name", "nt")
    with pytest.raises(NotImplementedError, match="not implemented on Windows"):
        LocalDirectoryCarrier(tmp_path / "carrier")
