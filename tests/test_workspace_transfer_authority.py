from pathlib import Path
import hashlib

import pytest

from fs_overlay.identity_verification import AuthenticatedPrincipal
from fs_overlay.storage_engine import LocalStorageEngine
from fs_overlay.workspace import WorkspaceBinding
from fs_overlay.workspace_migration import plan_export, plan_import
from fs_overlay.workspace_state import WorkspaceStateStore
from fs_overlay.workspace_transfer_authority import (
    TransferAuthorityScope,
    grant_authenticated_policy_bound_transfer_authority,
    grant_transfer_authority,
    validate_authenticated_transfer_authority,
)
from fs_overlay.authority_policy import AuthorityConstraints, AuthorityPrincipal, PolicyAuthorization
from fs_overlay.authority_revocation import AuthorityRevocationRegistry


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


def _authenticated_evidence(principal_id: str = "principal-1", issuer_id: str = "issuer-1") -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        principal_id=principal_id,
        issuer_id=issuer_id,
        node_id="node-1",
        key_id="key-1",
        key_fingerprint="a" * 64,
        trust_root_id="root-1",
        claims_digest=hashlib.sha256(b"claims").hexdigest(),
    )


def _authorized_plan(tmp_path: Path):
    _, _, plan = _state_and_plans(tmp_path)
    authorization = PolicyAuthorization(
        principal=AuthorityPrincipal("principal-1", "issuer-1"),
        constraints=AuthorityConstraints("destination", plan.snapshot_id),
        approved=True,
    )
    authority = grant_authenticated_policy_bound_transfer_authority(
        plan,
        transaction_id="tx-auth-revoke",
        scope=TransferAuthorityScope.MATERIALIZE,
        authorization=authorization,
        authenticated_principal=_authenticated_evidence(),
    )
    return authority


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


def test_authenticated_principal_must_match_policy(tmp_path: Path) -> None:
    _, _, plan = _state_and_plans(tmp_path)
    authorization = PolicyAuthorization(
        principal=AuthorityPrincipal("principal-1", "issuer-1"),
        constraints=AuthorityConstraints("destination", plan.snapshot_id),
        approved=True,
    )
    evidence = _authenticated_evidence(principal_id="principal-2")
    with pytest.raises(PermissionError, match="principal does not match"):
        grant_authenticated_policy_bound_transfer_authority(
            plan,
            transaction_id="tx-auth-1",
            scope=TransferAuthorityScope.MATERIALIZE,
            authorization=authorization,
            authenticated_principal=evidence,
        )


def test_authenticated_principal_binds_policy_authority(tmp_path: Path) -> None:
    _, _, plan = _state_and_plans(tmp_path)
    authorization = PolicyAuthorization(
        principal=AuthorityPrincipal("principal-1", "issuer-1"),
        constraints=AuthorityConstraints("destination", plan.snapshot_id),
        approved=True,
    )
    authority = grant_authenticated_policy_bound_transfer_authority(
        plan,
        transaction_id="tx-auth-2",
        scope=TransferAuthorityScope.MATERIALIZE,
        authorization=authorization,
        authenticated_principal=_authenticated_evidence(),
    )
    assert authority.principal_id == "principal-1"
    assert authority.issuer_id == "issuer-1"
    assert authority.authority_id is not None


def test_authenticated_authority_passes_before_revocation(tmp_path: Path) -> None:
    authority = _authorized_plan(tmp_path)
    registry = AuthorityRevocationRegistry(tmp_path / "revocations.jsonl")
    validate_authenticated_transfer_authority(
        authority,
        authenticated_principal=_authenticated_evidence(),
        revocations=registry,
    )


def test_authenticated_authority_rejects_principal_mismatch(tmp_path: Path) -> None:
    authority = _authorized_plan(tmp_path)
    registry = AuthorityRevocationRegistry(tmp_path / "revocations.jsonl")
    with pytest.raises(PermissionError, match="principal does not match transfer authority"):
        validate_authenticated_transfer_authority(
            authority,
            authenticated_principal=_authenticated_evidence(principal_id="principal-2"),
            revocations=registry,
        )


def test_authenticated_authority_rejects_issuer_mismatch(tmp_path: Path) -> None:
    authority = _authorized_plan(tmp_path)
    registry = AuthorityRevocationRegistry(tmp_path / "revocations.jsonl")
    with pytest.raises(PermissionError, match="issuer does not match transfer authority"):
        validate_authenticated_transfer_authority(
            authority,
            authenticated_principal=_authenticated_evidence(issuer_id="issuer-2"),
            revocations=registry,
        )


def test_authenticated_authority_rejects_revoked_authority(tmp_path: Path) -> None:
    authority = _authorized_plan(tmp_path)
    registry = AuthorityRevocationRegistry(tmp_path / "revocations.jsonl")
    registry.revoke(authority.authority_id, reason="operator revoked transfer")
    with pytest.raises(PermissionError, match="authority has been revoked"):
        validate_authenticated_transfer_authority(
            authority,
            authenticated_principal=_authenticated_evidence(),
            revocations=registry,
        )


def test_authenticated_authority_rejects_missing_provenance(tmp_path: Path) -> None:
    _, _, plan = _state_and_plans(tmp_path)
    authority = grant_transfer_authority(
        plan,
        transaction_id="tx-unbound",
        scope=TransferAuthorityScope.MATERIALIZE,
        approved=True,
    )
    registry = AuthorityRevocationRegistry(tmp_path / "revocations.jsonl")
    with pytest.raises(PermissionError, match="no durable authority identity"):
        validate_authenticated_transfer_authority(
            authority,
            authenticated_principal=_authenticated_evidence(),
            revocations=registry,
        )
