from pathlib import Path

import pytest

from fs_overlay.authority_policy import (
    AuthorityConstraints,
    AuthorityPrincipal,
    PolicyAuthorization,
    validate_policy_authorization,
)
from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_import
from fs_overlay.workspace_state import WorkspaceStateStore


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


def test_policy_authorization_requires_explicit_approval(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    authorization = PolicyAuthorization(
        AuthorityPrincipal("operator-1", "control-plane-1"),
        AuthorityConstraints("destination", plan.snapshot_id),
        approved=False,
    )
    with pytest.raises(PermissionError, match="did not explicitly authorize"):
        validate_policy_authorization(
            authorization,
            workspace_id="destination",
            snapshot_id=plan.snapshot_id,
        )


def test_policy_authorization_requires_exact_workspace_and_snapshot(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    authorization = PolicyAuthorization(
        AuthorityPrincipal("operator-1", "control-plane-1"),
        AuthorityConstraints("destination", plan.snapshot_id),
        approved=True,
    )
    with pytest.raises(PermissionError, match="workspace constraint"):
        validate_policy_authorization(
            authorization,
            workspace_id="other",
            snapshot_id=plan.snapshot_id,
        )
    with pytest.raises(PermissionError, match="snapshot constraint"):
        validate_policy_authorization(
            authorization,
            workspace_id="destination",
            snapshot_id="wrong-snapshot",
        )


def test_policy_constraints_cannot_enable_source_deletion() -> None:
    with pytest.raises(PermissionError, match="source deletion"):
        AuthorityConstraints("destination", "snapshot-1", allow_source_delete=True)


def test_policy_principal_requires_issuer_and_principal() -> None:
    with pytest.raises(ValueError, match="principal and issuer"):
        AuthorityPrincipal("", "issuer")
    with pytest.raises(ValueError, match="principal and issuer"):
        AuthorityPrincipal("principal", "")
