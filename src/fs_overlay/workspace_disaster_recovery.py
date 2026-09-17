"""Crash-safe logical workspace disaster recovery into a managed storage root.

Recovery copies only content-addressed objects named by a previously verified
workspace snapshot. The destination is rebuilt through ``LocalStorageEngine``
and is never treated as authoritative until every object and the resulting
snapshot commitment have been verified. Host workspace materialization remains
a separate authority-bearing concern.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .storage_engine import LocalStorageEngine
from .storage_resilience import MerkleDAG, Snapshot
from .workspace_state import WorkspaceState


class WorkspaceRecoveryError(RuntimeError):
    """Raised when a workspace cannot be reconstructed from its snapshot."""


@dataclass(frozen=True, slots=True)
class WorkspaceRecoveryResult:
    workspace_id: str
    snapshot_id: str
    object_count: int
    destination_root: Path
    verified: bool


class WorkspaceDisasterRecovery:
    """Reconstruct verified logical workspace state into a managed store."""

    def __init__(self, destination_root: str | Path) -> None:
        self.destination_root = Path(destination_root)

    @staticmethod
    def _validate_state(state: WorkspaceState) -> Snapshot:
        reasons = state.validate()
        if reasons:
            raise WorkspaceRecoveryError(",".join(reasons))
        snapshot = state.snapshot
        if MerkleDAG.root(snapshot.objects) != snapshot.merkle_root:
            raise WorkspaceRecoveryError("snapshot Merkle root verification failed")
        return snapshot

    def restore_from_engine(
        self,
        state: WorkspaceState,
        source_engine: LocalStorageEngine,
    ) -> WorkspaceRecoveryResult:
        """Copy every snapshot object and verify the reconstructed commitment."""
        snapshot = self._validate_state(state)
        destination = LocalStorageEngine(self.destination_root)
        restored: list[str] = []
        try:
            for object_id in snapshot.objects:
                data = source_engine.get(object_id)
                if destination.store.object_id(data) != object_id:
                    raise WorkspaceRecoveryError("recovered object identity mismatch")
                restored.append(destination.store.put(data))
        except (OSError, ValueError, IOError) as exc:
            raise WorkspaceRecoveryError("workspace object recovery failed") from exc

        restored_ids = tuple(sorted(restored))
        expected_ids = tuple(sorted(snapshot.objects))
        if restored_ids != expected_ids:
            raise WorkspaceRecoveryError("recovered object set does not match snapshot")
        if MerkleDAG.root(restored_ids) != snapshot.merkle_root:
            raise WorkspaceRecoveryError("recovered Merkle root does not match snapshot")
        for object_id in expected_ids:
            if destination.store.object_id(destination.store.get(object_id)) != object_id:
                raise WorkspaceRecoveryError("recovered object verification failed")

        return WorkspaceRecoveryResult(
            state.workspace_id,
            snapshot.snapshot_id,
            len(expected_ids),
            self.destination_root,
            True,
        )
