from pathlib import Path

import pytest

from fs_overlay.authority_policy import (
    AuthorityConstraints,
    AuthorityPrincipal,
    PolicyAuthorization,
)
from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_authority import (
    TransferAuthorityScope,
    grant_policy_bound_transfer_authority,
)


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


def _authorization(plan, *, approved=True, workspace_id=None, snapshot_id=None):
    return PolicyAuthorization(
        principal=AuthorityPrincipal("principal-1", "issuer-1"),
        constraints=AuthorityConstraints(
            workspace_id=workspace_id or plan.destination_workspace_id,
            snapshot_id=snapshot_id or plan.snapshot_id,
        ),
        approved=approved,
    )


def test_policy_bound_authority_carries_immutable_provenance(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    authority = grant_policy_bound_transfer_authority(
        plan,
        transaction_id="tx-policy-1",
        scope=TransferAuthorityScope.MATERIALIZE,
        authorization=_authorization(plan),
    )
    assert authority.principal_id == "principal-1"
    assert authority.issuer_id == "issuer-1"
    assert authority.policy_digest
    assert authority.authority_id
    assert len(authority.policy_digest) == 64
    assert len(authority.authority_id) == 64


def test_policy_bound_authority_rejects_unapproved_policy(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    with pytest.raises(PermissionError, match="explicitly authorize"):
        grant_policy_bound_transfer_authority(
            plan,
            transaction_id="tx-policy-2",
            scope=TransferAuthorityScope.MATERIALIZE,
            authorization=_authorization(plan, approved=False),
        )


def test_policy_bound_authority_rejects_wrong_workspace(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    authorization = _authorization(plan, workspace_id="other-workspace")
    with pytest.raises(PermissionError, match="workspace constraint"):
        grant_policy_bound_transfer_authority(
            plan,
            transaction_id="tx-policy-3",
            scope=TransferAuthorityScope.MATERIALIZE,
            authorization=authorization,
        )


def test_policy_bound_authority_rejects_wrong_snapshot(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    authorization = _authorization(plan, snapshot_id="other-snapshot")
    with pytest.raises(PermissionError, match="snapshot constraint"):
        grant_policy_bound_transfer_authority(
            plan,
            transaction_id="tx-policy-4",
            scope=TransferAuthorityScope.MATERIALIZE,
            authorization=authorization,
        )


def test_policy_bound_authority_digest_is_deterministic(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    first = grant_policy_bound_transfer_authority(
        plan,
        transaction_id="tx-policy-5",
        scope=TransferAuthorityScope.MATERIALIZE,
        authorization=_authorization(plan),
    )
    second = grant_policy_bound_transfer_authority(
        plan,
        transaction_id="tx-policy-5",
        scope=TransferAuthorityScope.MATERIALIZE,
        authorization=_authorization(plan),
    )
    assert first.policy_digest == second.policy_digest
    assert first.authority_id == second.authority_id
