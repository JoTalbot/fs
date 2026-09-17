"""Deterministic metadata redundancy primitives.

This module creates independently addressable metadata replicas and verifies
that a replica set agrees on one canonical metadata value. It does not claim
physical durability or substitute for an external replicated metadata store.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, Mapping


class MetadataCorruption(ValueError):
    """A metadata replica cannot be trusted as encoded."""


@dataclass(frozen=True, slots=True)
class MetadataReplica:
    replica_id: str
    digest: str
    payload: bytes


class MetadataRedundancy:
    """Build and verify a bounded set of deterministic metadata replicas."""

    def __init__(self, replica_count: int = 2) -> None:
        if type(replica_count) is not int or replica_count < 2:
            raise ValueError("metadata replica_count must be an integer >= 2")
        self.replica_count = replica_count

    @staticmethod
    def canonical(metadata: Mapping[str, str]) -> bytes:
        if not isinstance(metadata, Mapping) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in metadata.items()
        ):
            raise ValueError("metadata must be a string-to-string mapping")
        return json.dumps(dict(sorted(metadata.items())), sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _digest(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def create(self, metadata: Mapping[str, str]) -> tuple[MetadataReplica, ...]:
        payload = self.canonical(metadata)
        digest = self._digest(payload)
        return tuple(MetadataReplica(str(index), digest, payload) for index in range(self.replica_count))

    def verify(self, replicas: Iterable[MetadataReplica]) -> dict[str, str]:
        materialized = tuple(replicas)
        if len(materialized) < 2:
            raise MetadataCorruption("metadata redundancy requires at least two replicas")
        expected_digest = materialized[0].digest
        expected_payload = materialized[0].payload
        if not isinstance(expected_digest, str) or not isinstance(expected_payload, bytes):
            raise MetadataCorruption("metadata replica schema is invalid")
        if self._digest(expected_payload) != expected_digest:
            raise MetadataCorruption("metadata replica digest verification failed")
        for replica in materialized[1:]:
            if replica.digest != expected_digest or replica.payload != expected_payload:
                raise MetadataCorruption("metadata replica mismatch")
            if self._digest(replica.payload) != replica.digest:
                raise MetadataCorruption("metadata replica digest verification failed")
        try:
            decoded = json.loads(expected_payload)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
            raise MetadataCorruption("metadata replica JSON is invalid") from exc
        if not isinstance(decoded, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in decoded.items()
        ):
            raise MetadataCorruption("metadata replica schema is invalid")
        return dict(decoded)
