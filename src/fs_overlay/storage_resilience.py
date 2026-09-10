"""Failure-domain aware storage resilience primitives.

The module is deliberately dependency-free. It plans and records recovery; it does
not silently mutate arbitrary host storage or pretend that planning is execution.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from .storage_engine import Manifest, MerkleDAG, _canonical


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    generation: int
    objects: tuple[str, ...]
    merkle_root: str
    created_ns: int
    metadata: dict[str, str] | None = None

    def unsigned(self) -> dict[str, object]:
        return {
            "generation": self.generation,
            "objects": self.objects,
            "merkle_root": self.merkle_root,
            "created_ns": self.created_ns,
            "metadata": self.metadata,
        }

    def identity(self) -> str:
        return hashlib.sha256(_canonical(self.unsigned())).hexdigest()


class SnapshotStore:
    """Immutable, content-addressed snapshot catalog."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, objects: Iterable[str], *, generation: int, metadata: dict[str, str] | None = None) -> Snapshot:
        ordered = tuple(sorted(set(objects)))
        root = MerkleDAG.root(ordered)
        now = time.time_ns()
        unsigned = Snapshot("", generation, ordered, root, now, metadata)
        snapshot = Snapshot(unsigned.identity(), generation, ordered, root, now, metadata)
        self._write(snapshot)
        return snapshot

    def _write(self, snapshot: Snapshot) -> None:
        target = self.root / snapshot.snapshot_id
        if target.exists():
            if Snapshot.from_bytes(target.read_bytes()).identity() != snapshot.snapshot_id:
                raise IOError("snapshot collision or corruption")
            return
        fd, temporary = tempfile.mkstemp(prefix=".snapshot-", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(_canonical(asdict(snapshot)))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
            try:
                directory_fd = os.open(self.root, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                pass
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def get(self, snapshot_id: str) -> Snapshot:
        return Snapshot.from_bytes((self.root / snapshot_id).read_bytes())


# Bind parsing as a classmethod after the immutable representation is declared.
def _snapshot_from_bytes(cls, data: bytes) -> Snapshot:
    raw = json.loads(data)
    snapshot = cls(str(raw["snapshot_id"]), int(raw["generation"]), tuple(raw["objects"]),
                   str(raw["merkle_root"]), int(raw["created_ns"]), raw.get("metadata"))
    if snapshot.identity() != snapshot.snapshot_id:
        raise ValueError("snapshot identity verification failed")
    if MerkleDAG.root(snapshot.objects) != snapshot.merkle_root:
        raise ValueError("snapshot Merkle root verification failed")
    return snapshot

Snapshot.from_bytes = classmethod(_snapshot_from_bytes)  # type: ignore[attr-defined]


@dataclass(frozen=True)
class RecoveryNode:
    node_id: str
    object_id: str
    action: str
    dependencies: tuple[str, ...] = ()
    failure_domain: str | None = None


class RecoveryGraph:
    """Deterministic dependency graph used to order recovery actions."""

    def __init__(self, nodes: Iterable[RecoveryNode] = ()):
        self.nodes = {node.node_id: node for node in nodes}

    def add(self, node: RecoveryNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError("duplicate recovery node")
        missing = [dep for dep in node.dependencies if dep not in self.nodes]
        if missing:
            raise ValueError(f"unknown recovery dependency: {missing[0]}")
        self.nodes[node.node_id] = node

    def order(self) -> tuple[str, ...]:
        indegree = {node_id: 0 for node_id in self.nodes}
        children: dict[str, list[str]] = {node_id: [] for node_id in self.nodes}
        for node in self.nodes.values():
            for dependency in node.dependencies:
                indegree[node.node_id] += 1
                children[dependency].append(node.node_id)
        ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        result: list[str] = []
        while ready:
            current = ready.pop(0)
            result.append(current)
            for child in sorted(children[current]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
                    ready.sort()
        if len(result) != len(self.nodes):
            raise ValueError("recovery graph contains a cycle")
        return tuple(result)


@dataclass(frozen=True)
class CarrierState:
    carrier_id: str
    failure_domain: str
    capacity_bytes: int
    used_bytes: int
    healthy: bool = True
    approved: bool = True
    locality_score: float = 0.0

    @property
    def free_bytes(self) -> int:
        return max(0, self.capacity_bytes - self.used_bytes)


class PlacementPlanner:
    """Score approved carriers while explicitly penalizing failure-domain concentration."""

    def rank(self, carriers: Iterable[CarrierState], *, required_bytes: int = 0,
             excluded_domains: Iterable[str] = ()) -> tuple[CarrierState, ...]:
        excluded = set(excluded_domains)
        eligible = [c for c in carriers if c.approved and c.healthy and c.free_bytes >= required_bytes]
        def score(carrier: CarrierState) -> tuple[float, str]:
            capacity = carrier.free_bytes / max(1, carrier.capacity_bytes)
            diversity = 1.0 if carrier.failure_domain not in excluded else -1.0
            return (capacity * 0.55 + carrier.locality_score * 0.15 + diversity * 0.30, carrier.carrier_id)
        return tuple(sorted(eligible, key=score, reverse=True))


@dataclass(frozen=True)
class QuarantineRecord:
    carrier_id: str
    reason: str
    observed_hash: str | None
    expected_hash: str | None
    timestamp_ns: int
    record_id: str


class QuarantineLedger:
    """Append-only suspect-carrier records; quarantine never overwrites evidence."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def quarantine(self, carrier_id: str, *, reason: str, observed_hash: str | None = None,
                   expected_hash: str | None = None) -> QuarantineRecord:
        record = QuarantineRecord(carrier_id, reason, observed_hash, expected_hash, time.time_ns(), uuid.uuid4().hex)
        encoded = _canonical(asdict(record))
        with self.path.open("ab") as handle:
            handle.write(f"{len(encoded):016x}".encode() + encoded + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        return record

    def replay(self) -> tuple[QuarantineRecord, ...]:
        if not self.path.exists():
            return ()
        result: list[QuarantineRecord] = []
        with self.path.open("rb") as handle:
            for line in handle:
                if len(line) < 17:
                    continue
                try:
                    size, body = int(line[:16], 16), line[16:-1]
                    if len(body) != size:
                        continue
                    raw = json.loads(body)
                    result.append(QuarantineRecord(str(raw["carrier_id"]), str(raw["reason"]), raw.get("observed_hash"),
                                                   raw.get("expected_hash"), int(raw["timestamp_ns"]), str(raw["record_id"])))
                except (ValueError, json.JSONDecodeError, KeyError, TypeError):
                    continue
        return tuple(result)


def recovery_state(valid_shards: int, data_shards: int, *, repairing: bool = False) -> str:
    if valid_shards < 0 or data_shards <= 0:
        raise ValueError("invalid shard counts")
    if valid_shards < data_shards:
        return "UNRECOVERABLE"
    if repairing:
        return "REPAIRING"
    return "HEALTHY" if valid_shards >= data_shards else "DEGRADED"
