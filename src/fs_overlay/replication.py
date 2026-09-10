"""Authorized replica execution boundary.

Planning and execution are separate. The executor accepts only an explicit
adapter, verifies the copied content, and never discovers or mutates hosts by
itself.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol


class ReplicaAdapter(Protocol):
    def read(self, node_id: str, object_id: str) -> bytes: ...
    def write(self, node_id: str, object_id: str, data: bytes) -> None: ...


@dataclass(frozen=True)
class ReplicaAction:
    object_id: str
    source_node: str
    target_node: str
    expected_sha256: str


@dataclass(frozen=True)
class ReplicaResult:
    action: ReplicaAction
    status: str
    observed_sha256: str | None = None
    reason: str = ""


class ReplicaExecutor:
    """Execute one already-authorized replication action through an adapter."""

    def __init__(self, adapter: ReplicaAdapter):
        self.adapter = adapter

    def execute(self, action: ReplicaAction) -> ReplicaResult:
        data = self.adapter.read(action.source_node, action.object_id)
        observed = hashlib.sha256(data).hexdigest()
        if observed != action.expected_sha256:
            return ReplicaResult(action, "FAILED", observed, "source integrity verification failed")
        self.adapter.write(action.target_node, action.object_id, data)
        copied = self.adapter.read(action.target_node, action.object_id)
        copied_hash = hashlib.sha256(copied).hexdigest()
        if copied_hash != action.expected_sha256:
            return ReplicaResult(action, "FAILED", copied_hash, "target verification failed")
        return ReplicaResult(action, "SUCCEEDED", copied_hash, "replica verified")
