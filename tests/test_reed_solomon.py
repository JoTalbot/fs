from __future__ import annotations

import pytest

from fs_overlay.reed_solomon import ReedSolomonCoder


def test_reed_solomon_round_trip_and_recovery_from_multiple_missing_shards() -> None:
    coder = ReedSolomonCoder()
    data = [b"alpha", b"bravo", b"charl"]

    encoded = coder.encode(data, parity_shards=2)
    recovered = coder.recover([encoded[0], None, encoded[2], None, encoded[4]], data_shards=3, parity_shards=2)

    assert len(encoded) == 5
    assert recovered == data


def test_reed_solomon_is_deterministic() -> None:
    coder = ReedSolomonCoder()
    data = [b"0000", b"1111", b"2222", b"3333"]

    assert coder.encode(data, parity_shards=2) == coder.encode(data, parity_shards=2)


def test_reed_solomon_rejects_insufficient_or_malformed_input() -> None:
    coder = ReedSolomonCoder()

    with pytest.raises(ValueError, match="insufficient"):
        coder.recover([b"a", None, None], data_shards=2, parity_shards=1)

    with pytest.raises(ValueError, match="equal length"):
        coder.encode([b"a", b"bb"], parity_shards=1)

    with pytest.raises(TypeError, match="bytes"):
        coder.encode([b"a", "not-bytes"], parity_shards=1)  # type: ignore[list-item]


@pytest.mark.parametrize("data_shards,parity_shards", [(0, 1), (1, 0), (256, 1), (True, 1)])
def test_reed_solomon_rejects_invalid_counts(data_shards: object, parity_shards: object) -> None:
    coder = ReedSolomonCoder()
    with pytest.raises(ValueError):
        coder._validate_counts(data_shards, parity_shards)  # type: ignore[arg-type]


def test_reed_solomon_requires_exact_total_shard_count() -> None:
    with pytest.raises(ValueError, match="unexpected shard count"):
        ReedSolomonCoder().recover([b"a"], data_shards=1, parity_shards=1)
