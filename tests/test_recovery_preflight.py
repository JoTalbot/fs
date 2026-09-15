from pathlib import Path

import pytest

from fs_overlay.recovery_preflight import recovery_preflight
from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_journal import TransferJournalPhase, WorkspaceTransferJournal
from fs_overlay.workspace_transfer_recovery import (
    DestinationRecoveryState,
    TransferRecoveryEvidence,
)


class Verifier:
    def __init__(self, result=True):
        self.result = result
        self.calls = 0

    def verify(self, transaction, evidence):
        self.calls += 1
        return self.result


def _candidate(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "destination"
    destination.mkdir()
    engine = LocalStorageEngine(tmp_path / "storage")
    engine.put(b"payload")
    state = WorkspaceStateStore(tmp_path / "snapshots").create(
        WorkspaceBinding("source", str(source), owned_or_delegated=True), engine
    )
    plan = plan_import(
        state,
        WorkspaceBinding("destination", str(destination), owned_or_delegated=True),
    )
    journal = WorkspaceTransferJournal(tmp_path / "journal.log")
    transaction_id = journal.begin(plan)
    journal.mark(transaction_id, plan, TransferJournalPhase.MATERIALIZING)
    return journal.recovery_candidates()[0]


def _evidence(entry, **overrides):
    values = {
        "transaction_id": entry.transaction_id,
        "snapshot_id": entry.snapshot_id,
        "destination_state": DestinationRecoveryState.MATCHES_SNAPSHOT,
        "destination_verified": True,
        "mutation_complete": True,
        "source_preserved": True,
        "rollback_safe": False,
        "staging_absent": True,
    }
    values.update(overrides)
    return TransferRecoveryEvidence(**values)


def test_recovery_requires_independent_verifier(tmp_path: Path):
    entry = _candidate(tmp_path)
    verifier = Verifier(False)
    with pytest.raises(PermissionError, match="independently verified"):
        recovery_preflight(entry, _evidence(entry), evidence_verifier=verifier)
    assert verifier.calls == 1


def test_recovery_accepts_only_verified_evidence(tmp_path: Path):
    entry = _candidate(tmp_path)
    verifier = Verifier(True)
    result = recovery_preflight(entry, _evidence(entry), evidence_verifier=verifier)
    assert result.plan.decision.value == "commit_proven"
    assert result.plan.transaction_id == entry.transaction_id
    assert verifier.calls == 1


def test_recovery_verifier_failure_is_fail_closed(tmp_path: Path):
    entry = _candidate(tmp_path)

    class BrokenVerifier:
        def verify(self, transaction, evidence):
            raise RuntimeError("observer unavailable")

    with pytest.raises(PermissionError, match="verification failed"):
        recovery_preflight(entry, _evidence(entry), evidence_verifier=BrokenVerifier())


def test_recovery_rejects_prepared_transaction_before_verifier(tmp_path: Path):
    entry = _candidate(tmp_path)
    prepared = entry.__class__(
        entry.transaction_id,
        TransferJournalPhase.PREPARED,
        entry.operation,
        entry.snapshot_id,
        entry.source_workspace_id,
        entry.destination_workspace_id,
    )
    verifier = Verifier()
    with pytest.raises(PermissionError, match="materializing"):
        recovery_preflight(prepared, _evidence(entry), evidence_verifier=verifier)
    assert verifier.calls == 0


def test_recovery_rejects_identity_mismatch_before_verifier(tmp_path: Path):
    entry = _candidate(tmp_path)
    verifier = Verifier()
    with pytest.raises(PermissionError, match="transaction"):
        recovery_preflight(
            entry,
            _evidence(entry, transaction_id="wrong"),
            evidence_verifier=verifier,
        )
    assert verifier.calls == 0
