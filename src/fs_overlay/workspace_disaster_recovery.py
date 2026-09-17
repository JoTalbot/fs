"""Crash-safe logical workspace disaster recovery into a managed storage root.

Recovery copies the content-addressed manifest and all of its chunks named by a
previously verified workspace snapshot. The destination inventory is published
only through the normal storage commit path, and every reconstructed manifest
is verified before the recovery result is returned. Host workspace
materialization remains a separate authority-bearing concern.
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
        if snapshot.identity() != snapshot.snapshot_id:
            raise WorkspaceRecoveryError("snapshot identity verification failed")
        return snapshot

    def restore_from_engine(
        self,
        state: WorkspaceState,
        source_engine: LocalStorageEngine,
    ) -> WorkspaceRecoveryResult:
        """Copy every snapshot manifest and chunk, then verify the result."""
        snapshot = self._validate_state(state)
        destination = LocalStorageEngine(self.destination_root, chunk_size=source_engine.chunker.chunk_size)
        restored: list[str] = []
        try:
            for object_id in snapshot.objects:
                manifest = source_engine.store.get_manifest(object_id)
                for chunk_id in manifest.chunks:
                    chunk = source_engine.store.get(chunk_id)
                    if destination.store.object_id(chunk) != chunk_id:
                        raise WorkspaceRecoveryError("recovered chunk identity mismatch")
                    destination.store.put(chunk)
                if manifest.identity() != object_id:
                    raise WorkspaceRecoveryError("recovered manifest identity mismatch")
                destination._commit_manifest(manifest)
                restored.append(manifest.object_id)
                if destination.get(object_id) != source_engine.get(object_id):
                    raise WorkspaceRecoveryError("recovered object content mismatch")
        except WorkspaceRecoveryError:
            raise
        except (OSError, ValueError, IOError) as exc:
            raise WorkspaceRecoveryError("workspace object recovery failed") from exc

        restored_ids = tuple(sorted(restored))
        expected_ids = tuple(sorted(snapshot.objects))
        if restored_ids != expected_ids:
            raise WorkspaceRecoveryError("recovered object set does not match snapshot")
        if MerkleDAG.root(restored_ids) != snapshot.merkle_root:
            raise WorkspaceRecoveryError("recovered Merkle root does not match snapshot")
        audit = destination.audit()
        if audit != {"ok": True, "objects_checked": len(expected_ids), "corrupt_objects": []}:
            raise WorkspaceRecoveryError("recovered workspace audit failed")

        return WorkspaceRecoveryResult(
            state.workspace_id,
            snapshot.snapshot_id,
            len(expected_ids),
            self.destination_root,
            True,
        )
