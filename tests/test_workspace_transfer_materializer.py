from pathlib import Path

import pytest

from fs_overlay.authority_revocation import AuthorityRevocationRegistry
from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_authority import (
    TransferAuthority,
    TransferAuthorityScope,
    grant_transfer_authority,
)
from fs_overlay.workspace_transfer_journal import (
    TransferJournalPhase,
    WorkspaceTransferJournal,
)
from fs_overlay.workspace_transfer_materializer import validate_materialization_preflight


def _plan(tmp_path: Path):
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


def test_materializer_preflight_requires_exact_authority_and_journal(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "journal.log"
    journal = WorkspaceTransferJournal(path)
    transaction_id = journal.begin(plan)
    authority = grant_transfer_authority(
        plan,
        transaction_id=transaction_id,
        scope=TransferAuthorityScope.MATERIALIZE,
        approved=True,
    )

    preflight = validate_materialization_preflight(plan, authority, journal)
    assert preflight.transaction_id == transaction_id
    assert preflight.snapshot_id == plan.snapshot_id
    assert preflight.destination_workspace_id == "destination"
    assert preflight.source_preserved is True


def test_materializer_preflight_accepts_resumable_materializing_state(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    journal.mark(transaction_id, plan, TransferJournalPhase.MATERIALIZING)
    authority = grant_transfer_authority(
        plan,
        transaction_id=transaction_id,
        scope=TransferAuthorityScope.MATERIALIZE,
        approved=True,
    )
    assert validate_materialization_preflight(plan, authority, journal).operation is plan.operation


def test_materializer_preflight_rejects_wrong_scope(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    authority = TransferAuthority(
        transaction_id=transaction_id,
        snapshot_id=plan.snapshot_id,
        source_workspace_id=plan.source_workspace_id,
        destination_workspace_id=plan.destination_workspace_id,
        scope=TransferAuthorityScope.EXPORT,
    )
    with pytest.raises(PermissionError, match="materialize authority"):
        validate_materialization_preflight(plan, authority, journal)


def test_materializer_preflight_rejects_non_authority_decision(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    fake_decision = object()
    with pytest.raises(PermissionError, match="issued transfer authority"):
        validate_materialization_preflight(plan, fake_decision, journal)  # type: ignore[arg-type]


def test_materializer_preflight_rejects_authority_identity_mismatch(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    authority = TransferAuthority(
        transaction_id=transaction_id,
        snapshot_id="wrong-snapshot",
        source_workspace_id=plan.source_workspace_id,
        destination_workspace_id=plan.destination_workspace_id,
        scope=TransferAuthorityScope.MATERIALIZE,
    )
    with pytest.raises(PermissionError, match="does not match transfer plan"):
        validate_materialization_preflight(plan, authority, journal)


def test_materializer_preflight_rejects_terminal_transaction(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    journal.mark(transaction_id, plan, TransferJournalPhase.ABORTED)
    authority = grant_transfer_authority(
        plan,
        transaction_id=transaction_id,
        scope=TransferAuthorityScope.MATERIALIZE,
        approved=True,
    )
    with pytest.raises(ValueError, match="not in a materializable journal state"):
        validate_materialization_preflight(plan, authority, journal)


def test_materializer_preflight_rejects_revoked_authority(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    authority = TransferAuthority(
        transaction_id=transaction_id,
        snapshot_id=plan.snapshot_id,
        source_workspace_id=plan.source_workspace_id,
        destination_workspace_id=plan.destination_workspace_id,
        scope=TransferAuthorityScope.MATERIALIZE,
        authority_id="authority-1",
    )
    revocations = AuthorityRevocationRegistry(tmp_path / "revocations.log")
    revocations.revoke("authority-1", reason="cancelled")
    with pytest.raises(PermissionError, match="revoked"):
        validate_materialization_preflight(plan, authority, journal, revocations)


def test_materializer_preflight_requires_provenance_for_revocation_check(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    authority = grant_transfer_authority(
        plan,
        transaction_id=transaction_id,
        scope=TransferAuthorityScope.MATERIALIZE,
        approved=True,
    )
    revocations = AuthorityRevocationRegistry(tmp_path / "revocations.log")
    with pytest.raises(PermissionError, match="authority provenance"):
        validate_materialization_preflight(plan, authority, journal, revocations)
