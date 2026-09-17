"""Dependency-free Reed-Solomon erasure coding over GF(256).

The implementation is intentionally small and deterministic. It is a storage
primitive, not a claim of production durability by itself: callers still need
independent failure domains, authenticated shards, and deployment evidence.
"""
from __future__ import annotations

from typing import Sequence

_PRIMITIVE_POLY = 0x11D


def _gf_mul(left: int, right: int) -> int:
    result = 0
    while right:
        if right & 1:
            result ^= left
        right >>= 1
        left <<= 1
        if left & 0x100:
            left ^= _PRIMITIVE_POLY
    return result


def _gf_pow(value: int, exponent: int) -> int:
    result = 1
    while exponent:
        if exponent & 1:
            result = _gf_mul(result, value)
        value = _gf_mul(value, value)
        exponent >>= 1
    return result


def _gf_inv(value: int) -> int:
    if value == 0:
        raise ValueError("GF(256) zero has no multiplicative inverse")
    return _gf_pow(value, 254)


def _matrix_inverse(matrix: list[list[int]]) -> list[list[int]]:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    work = [row[:] + [1 if row_index == column else 0 for column in range(size)]
            for row_index, row in enumerate(matrix)]
    for column in range(size):
        pivot = next((row for row in range(column, size) if work[row][column]), None)
        if pivot is None:
            raise ValueError("matrix is singular")
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
        inverse = _gf_inv(work[column][column])
        work[column] = [_gf_mul(value, inverse) for value in work[column]]
        for row in range(size):
            if row == column or work[row][column] == 0:
                continue
            factor = work[row][column]
            work[row] = [left ^ _gf_mul(factor, right) for left, right in zip(work[row], work[column])]
    return [row[size:] for row in work]


def _matrix_multiply_rows(matrix: Sequence[Sequence[int]], shards: Sequence[bytes], size: int) -> list[bytes]:
    result: list[bytes] = []
    for row in matrix:
        output = bytearray(size)
        for coefficient, shard in zip(row, shards):
            if coefficient == 0:
                continue
            for index, value in enumerate(shard):
                output[index] ^= _gf_mul(coefficient, value)
        result.append(bytes(output))
    return result


class ReedSolomonCoder:
    """Systematic Reed-Solomon coder with deterministic recovery."""

    name = "reed-solomon-gf256"

    @staticmethod
    def _validate_counts(data_shards: int, parity_shards: int) -> None:
        if type(data_shards) is not int or data_shards <= 0:
            raise ValueError("data_shards must be a positive integer")
        if type(parity_shards) is not int or parity_shards <= 0:
            raise ValueError("parity_shards must be a positive integer")
        if data_shards + parity_shards > 256:
            raise ValueError("total shard count must not exceed 256")

    @staticmethod
    def _validate_shards(shards: Sequence[bytes], expected: int | None = None) -> int:
        if expected is not None and len(shards) != expected:
            raise ValueError("unexpected shard count")
        if not shards:
            raise ValueError("at least one shard is required")
        if any(not isinstance(shard, bytes) for shard in shards):
            raise TypeError("shards must contain bytes")
        size = len(shards[0])
        if any(len(shard) != size for shard in shards):
            raise ValueError("all shards must have equal length")
        return size

    @staticmethod
    def _matrix(data_shards: int, total_shards: int) -> list[list[int]]:
        # The first data_shards rows are the identity matrix, making the
        # encoding systematic. Remaining rows are Vandermonde rows.
        matrix: list[list[int]] = []
        for row in range(total_shards):
            if row < data_shards:
                matrix.append([1 if column == row else 0 for column in range(data_shards)])
            else:
                base = row - data_shards + 1
                matrix.append([_gf_pow(base, column) for column in range(data_shards)])
        return matrix

    def encode(self, shards: list[bytes], *, parity_shards: int) -> list[bytes]:
        data_shards = len(shards)
        self._validate_counts(data_shards, parity_shards)
        size = self._validate_shards(shards)
        matrix = self._matrix(data_shards, data_shards + parity_shards)
        return _matrix_multiply_rows(matrix, shards, size)

    def recover(
        self,
        shards: list[bytes | None],
        *,
        data_shards: int,
        parity_shards: int,
    ) -> list[bytes]:
        self._validate_counts(data_shards, parity_shards)
        total = data_shards + parity_shards
        if len(shards) != total:
            raise ValueError("unexpected shard count")
        available = [shard for shard in shards if shard is not None]
        if len(available) < data_shards:
            raise ValueError("insufficient shards for recovery")
        size = self._validate_shards(available[:data_shards])
        if any(shard is not None and len(shard) != size for shard in shards):
            raise ValueError("all shards must have equal length")

        matrix = self._matrix(data_shards, total)
        selected_indices = [index for index, shard in enumerate(shards) if shard is not None][:data_shards]
        selected_shards = [shards[index] for index in selected_indices]
        # The availability check above guarantees these are bytes.
        selected_matrix = [matrix[index] for index in selected_indices]
        inverse = _matrix_inverse(selected_matrix)
        recovered_data = _matrix_multiply_rows(inverse, [shard for shard in selected_shards if shard is not None], size)
        return recovered_data
