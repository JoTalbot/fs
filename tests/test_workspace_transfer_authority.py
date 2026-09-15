from pathlib import Path

import pytest

from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_export, plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_authority import (
    TransferAuthorityScope,
    grant_transfer_authority,
)


def _state_and_plans(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "destination"
    destination.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    engine.put(b"payload")
    state = WorkspaceStateStore(tmp_path / "snapshots").create(
        WorkspaceBinding("source", str(source), owned_or_delegated=True), engine
    )
    source_binding = WorkspaceBinding("source", str(source), owned_or_delegated=True)
    destination_binding = WorkspaceBinding("destination", str(destination), owned_or_delegated=True)
    return state, plan_export(state, source_binding), plan_import(state, destination_binding)


def test_authority_requires_explicit_approval(tmp_path: Path) -> None:
    _, _, plan = _state_and_plans(tmp_path)
    with pytest.raises(PermissionError, match="explicitly approved"):
        grant_transfer_authority(
            plan,
            transaction_id="tx-1",
            scope=TransferAuthorityScope.MATERIALIZE,
            approved=False,
        )


def test_materialization_authority_is_bound_to_exact_plan(tmp_path: Path) -> None:
    _, _, plan = _state_and_plans(tmp_path)
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


def test_export_authority_requires_export_plan(tmp_path: Path) -> None:
    _, export_plan, import_plan = _state_and_plans(tmp_path)
    authority = grant_transfer_authority(
        export_plan,
        transaction_id="tx-2",
        scope=TransferAuthorityScope.EXPORT,
        approved=True,
    )
    assert authority.scope is TransferAuthorityScope.EXPORT
    with pytest.raises(ValueError, match="export plan"):
        grant_transfer_authority(
            import_plan,
            transaction_id="tx-3",
            scope=TransferAuthorityScope.EXPORT,
            approved=True,
        )


def test_materialization_authority_rejects_export_plan(tmp_path: Path) -> None:
    _, export_plan, _ = _state_and_plans(tmp_path)
    with pytest.raises(ValueError, match="import or migration"):
        grant_transfer_authority(
            export_plan,
            transaction_id="tx-4",
            scope=TransferAuthorityScope.MATERIALIZE,
            approved=True,
        )
