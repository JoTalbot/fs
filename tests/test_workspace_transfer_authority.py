from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_authority import (
    TransferAuthorityScope,
    grant_transfer_authority,
)


def _ready_plan(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "destination"
    destination.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    engine.put(b"payload")
    state = WorkspaceStateStore(tmp_path / "snapshots").create(
        WorkspaceBinding("source", str(source), owned_or_delegated=True), engine
    )
    return plan_import(
        state,
        WorkspaceBinding("destination", str(destination), owned_or_delegated=True),
    )


def test_authority_requires_explicit_approval(tmp_path: Path) -> None:
    plan = _ready_plan(tmp_path)
    with pytest.raises(PermissionError, match="explicitly approved"):
        grant_transfer_authority(
            plan,
            transaction_id="tx-1",
            scope=TransferAuthorityScope.MATERIALIZE,
            approved=False,
        )


def test_authority_is_bound_to_exact_plan(tmp_path: Path) -> None:
    plan = _ready_plan(tmp_path)
    authority = grant_transfer_authority(
        plan,
        transaction_id="tx-1",
        scope=TransferAuthorityScope.MATERIALIZE,
        approved=True,
    )
    assert authority.transaction_id == "tx-1"
    assert authority.snapshot_id == plan.snapshot_id
    assert authority.source_workspace_id == plan.source_workspace_id
    assert authority.destination_workspace_id == plan.destination_workspace_id
    assert authority.source_preserved is True


def test_authority_rejects_unready_plan(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    state = WorkspaceStateStore(tmp_path / "snapshots").create(
        WorkspaceBinding("source", str(source), owned_or_delegated=True), engine
    )
    plan = plan_import(state, WorkspaceBinding("destination", "/missing", owned_or_delegated=True))
    with pytest.raises(ValueError, match="unready"):
        grant_transfer_authority(
            plan,
            transaction_id="tx-1",
            scope=TransferAuthorityScope.MATERIALIZE,
            approved=True,
        )


def test_export_authority_does_not_require_destination(tmp_path: Path) -> None:
    plan = _ready_plan(tmp_path)
    authority = grant_transfer_authority(
        plan,
        transaction_id="tx-2",
        scope=TransferAuthorityScope.EXPORT,
        approved=True,
    )
    assert authority.scope is TransferAuthorityScope.EXPORT
