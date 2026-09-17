"""Carrier discovery safety policy qualification."""
from __future__ import annotations

from pathlib import Path

import pytest

from fs_overlay.policy import CarrierPolicy

_PAYLOAD = b"x" * 4096


def _write(path: Path, payload: bytes = _PAYLOAD) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def test_allowed_file_inside_declared_root_is_admitted(tmp_path: Path) -> None:
    policy = CarrierPolicy(roots=(tmp_path,))
    target = _write(tmp_path / "carrier" / "payload.log")

    assert policy.is_allowed(target) is True


def test_file_outside_every_declared_root_is_rejected(tmp_path: Path) -> None:
    inside = tmp_path / "inside"
    outside = tmp_path / "outside"
    policy = CarrierPolicy(roots=(inside,))
    target = _write(outside / "payload.log")

    assert policy.is_allowed(target) is False


def test_empty_root_set_rejects_everything(tmp_path: Path) -> None:
    policy = CarrierPolicy(roots=())
    target = _write(tmp_path / "payload.log")

    assert policy.is_allowed(target) is False


def test_denied_component_is_rejected_even_with_allowed_suffix(tmp_path: Path) -> None:
    policy = CarrierPolicy(roots=(tmp_path,))
    target = _write(tmp_path / ".ssh" / "id_rsa.log")

    assert policy.is_allowed(target) is False


def test_denied_name_match_is_rejected(tmp_path: Path) -> None:
    policy = CarrierPolicy(roots=(tmp_path,), denied_names=frozenset({"forbidden.log"}))
    target = _write(tmp_path / "forbidden.log")

    assert policy.is_allowed(target) is False


def test_suffix_outside_allowlist_is_rejected(tmp_path: Path) -> None:
    policy = CarrierPolicy(roots=(tmp_path,))
    target = _write(tmp_path / "payload.txt")

    assert policy.is_allowed(target) is False


def test_files_outside_size_limits_are_rejected(tmp_path: Path) -> None:
    policy = CarrierPolicy(roots=(tmp_path,), min_file_size=4096, max_file_size=8192)
    too_small = _write(tmp_path / "small.log", b"x" * 4095)
    too_large = _write(tmp_path / "large.log", b"x" * 8193)
    in_range = _write(tmp_path / "exact.log", b"x" * 8192)

    assert policy.is_allowed(too_small) is False
    assert policy.is_allowed(too_large) is False
    assert policy.is_allowed(in_range) is True


def test_missing_path_and_directory_are_rejected(tmp_path: Path) -> None:
    policy = CarrierPolicy(roots=(tmp_path,))
    directory = tmp_path / "nested.log"
    directory.mkdir()

    assert policy.is_allowed(tmp_path / "absent.log") is False
    assert policy.is_allowed(directory) is False


@pytest.mark.parametrize("ratio", [0.0, -0.1, 0.31, 1.0])
def test_overhead_ratio_outside_bounds_is_rejected(ratio: float) -> None:
    with pytest.raises(ValueError):
        CarrierPolicy(roots=(), max_overhead_ratio=ratio)


def test_inconsistent_file_size_limits_are_rejected() -> None:
    with pytest.raises(ValueError):
        CarrierPolicy(roots=(), min_file_size=-1)
    with pytest.raises(ValueError):
        CarrierPolicy(roots=(), min_file_size=1024, max_file_size=512)


def test_capacity_for_respects_minimum_ratio_and_ceiling(tmp_path: Path) -> None:
    policy = CarrierPolicy(roots=(tmp_path,))
    capped = CarrierPolicy(roots=(tmp_path,), min_file_size=0, max_file_size=1000)

    assert policy.capacity_for(4095) == 0
    assert policy.capacity_for(10_000) == 3000
    assert capped.capacity_for(10_000) == 1000
