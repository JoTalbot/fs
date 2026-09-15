"""Explicit authority boundary for future workspace transfer materialization.

This module is deliberately contract-only: creating an authority token requires
an already verified transfer plan and an explicit caller decision. The token is
not inferred from filesystem capabilities and performs no filesystem mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from .authority_policy import PolicyAuthorization, validate_policy_authorization
from .authority_revocation import AuthorityRevocationRegistry
from .identity_verification import AuthenticatedPrincipal
from .workspace_migration import WorkspaceTransfer, WorkspaceTransferPlan


class TransferAuthorityScope(str, Enum):
    """The only mutation scopes that may be explicitly granted later."""

    MATERIALIZE = "materialize"
    EXPORT = "export"


@dataclass(frozen=True, slots=True)
class TransferAuthority:
    """Non-secret, auditable authority grant bound to one exact transfer plan."""

    transaction_id: str
    snapshot_id: str
    source_workspace_id: str
    destination_workspace_id: str | None
    scope: TransferAuthorityScope
    source_preserved: bool = True
    principal_id: str | None = None
    issuer_id: str | None = None
    policy_digest: str | None = None
    authority_id: str | None = None


def _policy_digest(authorization: PolicyAuthorization) -> str:
    """Return a deterministic non-secret digest of the policy decision inputs."""
    canonical = {
        "principal_id": authorization.principal.principal_id,
        "issuer_id": authorization.principal.issuer_id,
        "workspace_id": authorization.constraints.workspace_id,
        "snapshot_id": authorization.constraints.snapshot_id,
        "allow_source_delete": authorization.constraints.allow_source_delete,
        "allow_network": authorization.constraints.allow_network,
        "approved": authorization.approved,
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _authority_id(
    *,
    transaction_id: str,
    snapshot_id: str,
    source_workspace_id: str,
    destination_workspace_id: str | None,
    scope: TransferAuthorityScope,
    principal_id: str,
    issuer_id: str,
    policy_digest: str,
) -> str:
    """Derive stable authority provenance without treating the digest as auth."""
    canonical = {
        "transaction_id": transaction_id,
        "snapshot_id": snapshot_id,
        "source_workspace_id": source_workspace_id,
        "destination_workspace_id": destination_workspace_id,
        "scope": scope.value,
        "principal_id": principal_id,
        "issuer_id": issuer_id,
        "policy_digest": policy_digest,
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def grant_transfer_authority(
    plan: WorkspaceTransferPlan,
    *,
    transaction_id: str,
    scope: TransferAuthorityScope,
    approved: bool,
) -> TransferAuthority:
    """Create an explicit authority token; never infer authority from capability.

    ``approved`` is intentionally supplied by the caller. A future policy layer
    may derive this decision from an authenticated principal, but this primitive
    must never turn path access, ownership discovery, or capability detection
    into permission on its own.
    """
    if not approved:
        raise PermissionError("transfer authority was not explicitly approved")
    if not plan.ready:
        raise ValueError("cannot grant authority for an unready transfer plan")
    if not transaction_id:
        raise ValueError("transaction_id is required")
    if scope is TransferAuthorityScope.EXPORT and plan.operation is not WorkspaceTransfer.EXPORT:
        raise ValueError("export authority requires an export plan")
    if scope is TransferAuthorityScope.MATERIALIZE and plan.operation is WorkspaceTransfer.EXPORT:
        raise ValueError("materialization authority requires an import or migration plan")
    if scope is TransferAuthorityScope.MATERIALIZE and plan.destination_path is None:
        raise ValueError("materialization authority requires a destination")
    return TransferAuthority(
        transaction_id=transaction_id,
        snapshot_id=plan.snapshot_id,
        source_workspace_id=plan.source_workspace_id,
        destination_workspace_id=plan.destination_workspace_id,
        scope=scope,
        source_preserved=plan.source_preserved,
    )


def grant_policy_bound_transfer_authority(
    plan: WorkspaceTransferPlan,
    *,
    transaction_id: str,
    scope: TransferAuthorityScope,
    authorization: PolicyAuthorization,
) -> TransferAuthority:
    """Issue authority only after exact policy authorization has been validated."""
    workspace_id = (
        plan.destination_workspace_id
        if scope is TransferAuthorityScope.MATERIALIZE
        else plan.source_workspace_id
    )
    validate_policy_authorization(
        authorization,
        workspace_id=workspace_id,
        snapshot_id=plan.snapshot_id,
    )
    base = grant_transfer_authority(
        plan,
        transaction_id=transaction_id,
        scope=scope,
        approved=True,
    )
    policy_digest = _policy_digest(authorization)
    authority_id = _authority_id(
        transaction_id=base.transaction_id,
        snapshot_id=base.snapshot_id,
        source_workspace_id=base.source_workspace_id,
        destination_workspace_id=base.destination_workspace_id,
        scope=base.scope,
        principal_id=authorization.principal.principal_id,
        issuer_id=authorization.principal.issuer_id,
        policy_digest=policy_digest,
    )
    return TransferAuthority(
        transaction_id=base.transaction_id,
        snapshot_id=base.snapshot_id,
        source_workspace_id=base.source_workspace_id,
        destination_workspace_id=base.destination_workspace_id,
        scope=base.scope,
        source_preserved=base.source_preserved,
        principal_id=authorization.principal.principal_id,
        issuer_id=authorization.principal.issuer_id,
        policy_digest=policy_digest,
        authority_id=authority_id,
    )


def grant_authenticated_policy_bound_transfer_authority(
    plan: WorkspaceTransferPlan,
    *,
    transaction_id: str,
    scope: TransferAuthorityScope,
    authorization: PolicyAuthorization,
    authenticated_principal: AuthenticatedPrincipal,
) -> TransferAuthority:
    """Bind a policy authorization to independently verified identity evidence."""
    if authenticated_principal.principal_id != authorization.principal.principal_id:
        raise PermissionError("authenticated principal does not match policy principal")
    if authenticated_principal.issuer_id != authorization.principal.issuer_id:
        raise PermissionError("authenticated issuer does not match policy issuer")
    return grant_policy_bound_transfer_authority(
        plan,
        transaction_id=transaction_id,
        scope=scope,
        authorization=authorization,
    )


def validate_policy_bound_transfer_authority(
    authority: TransferAuthority,
    *,
    policy: PolicyAuthorization,
    authenticated_principal: AuthenticatedPrincipal,
) -> None:
    """Verify that authority provenance still represents this exact policy decision."""
    if not authority.policy_digest or not authority.authority_id:
        raise PermissionError("transfer authority has incomplete policy provenance")
    if authority.principal_id != policy.principal.principal_id:
        raise PermissionError("transfer authority principal does not match policy")
    if authority.issuer_id != policy.principal.issuer_id:
        raise PermissionError("transfer authority issuer does not match policy")
    if authenticated_principal.principal_id != authority.principal_id:
        raise PermissionError("authenticated principal does not match transfer authority")
    if authenticated_principal.issuer_id != authority.issuer_id:
        raise PermissionError("authenticated issuer does not match transfer authority")
    expected_digest = _policy_digest(policy)
    if authority.policy_digest != expected_digest:
        raise PermissionError("transfer authority policy provenance does not match authorization")
    expected_id = _authority_id(
        transaction_id=authority.transaction_id,
        snapshot_id=authority.snapshot_id,
        source_workspace_id=authority.source_workspace_id,
        destination_workspace_id=authority.destination_workspace_id,
        scope=authority.scope,
        principal_id=authority.principal_id,
        issuer_id=authority.issuer_id,
        policy_digest=authority.policy_digest,
    )
    if authority.authority_id != expected_id:
        raise PermissionError("transfer authority identity provenance is invalid")


def validate_authenticated_transfer_authority(
    authority: TransferAuthority,
    *,
    authenticated_principal: AuthenticatedPrincipal,
    revocations: AuthorityRevocationRegistry,
) -> None:
    """Fail closed before authority use unless identity and revocation agree."""
    if not authority.authority_id:
        raise PermissionError("transfer authority has no durable authority identity")
    if not authority.principal_id or not authority.issuer_id:
        raise PermissionError("transfer authority has incomplete identity provenance")
    if authenticated_principal.principal_id != authority.principal_id:
        raise PermissionError("authenticated principal does not match transfer authority")
    if authenticated_principal.issuer_id != authority.issuer_id:
        raise PermissionError("authenticated issuer does not match transfer authority")
    if revocations.is_revoked(authority.authority_id):
        raise PermissionError("transfer authority has been revoked")
