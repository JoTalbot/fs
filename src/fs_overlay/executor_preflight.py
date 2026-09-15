"""Unified fail-closed preflight for a future transfer executor.

This module composes existing security boundaries without implementing
cryptography or host filesystem mutation. A successful preflight returns only
non-host authority to proceed with an injected executor; callers still need a
separate transactional materializer implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .authority_policy import PolicyAuthorization, validate_policy_authorization
from .authority_revocation import AuthorityRevocationRegistry
from .identity_preflight import identity_preflight
from .identity_verification import AuthenticatedPrincipal, PrincipalVerifier, TrustRootStore
from .production_adapters import AuthenticatedTransport, KeyAdmission, NodeAdmission
from .transport_gate import FailClosedTransportGate
from .workspace_migration import WorkspaceTransferPlan
from .workspace_transfer_authority import (
    TransferAuthority,
    TransferAuthorityScope,
    validate_authenticated_transfer_authority,
)
from .workspace_transfer_journal import TransferJournalEntry, TransferJournalPhase
from .workspace_transfer_recovery import TransferRecoveryPlan


@dataclass(frozen=True, slots=True)
class ExecutorPreflightResult:
    """Validated executor inputs; no filesystem capability is implied."""

    principal: AuthenticatedPrincipal
    authority: TransferAuthority
    transport: FailClosedTransportGate
    transaction_id: str
    recovery: TransferRecoveryPlan | None = None


def executor_preflight(
    plan: WorkspaceTransferPlan,
    *,
    transaction: TransferJournalEntry,
    authority: TransferAuthority,
    policy: PolicyAuthorization,
    principal_verifier: PrincipalVerifier,
    trust_roots: TrustRootStore,
    node_admission: NodeAdmission,
    key_admission: KeyAdmission,
    transport: AuthenticatedTransport,
    revocations: AuthorityRevocationRegistry,
    principal_id: str,
    issuer_id: str,
    node_id: str,
    key_id: str,
    key_fingerprint: str,
    claims: Mapping[str, object],
    signature: bytes,
    recovery: TransferRecoveryPlan | None = None,
) -> ExecutorPreflightResult:
    """Require every executor security gate before any future mutation.

    Ordering is deliberate and fail-closed:
    trust root/identity -> node/key admission -> authenticated transport ->
    policy -> authority -> durable authority revocation -> transaction/recovery.
    The transport provider remains responsible for authenticated encryption and
    peer authentication; this function only binds that session to the verified
    principal.
    """
    if not plan.ready:
        raise PermissionError("executor preflight requires a ready transfer plan")

    principal = identity_preflight(
        principal_verifier,
        principal_id=principal_id,
        issuer_id=issuer_id,
        node_id=node_id,
        key_id=key_id,
        key_fingerprint=key_fingerprint,
        claims=claims,
        signature=signature,
        trust_roots=trust_roots,
        node_admission=node_admission,
        key_admission=key_admission,
    )

    transport_gate = FailClosedTransportGate(transport, principal)
    transport_gate.validate_session()

    scope_workspace = (
        plan.destination_workspace_id
        if authority.scope is TransferAuthorityScope.MATERIALIZE
        else plan.source_workspace_id
    )
    validate_policy_authorization(
        policy,
        workspace_id=scope_workspace,
        snapshot_id=plan.snapshot_id,
    )

    if authority.transaction_id != transaction.transaction_id:
        raise PermissionError("transfer authority transaction does not match journal")
    if authority.snapshot_id != plan.snapshot_id:
        raise PermissionError("transfer authority snapshot does not match plan")
    if authority.source_workspace_id != plan.source_workspace_id:
        raise PermissionError("transfer authority source does not match plan")
    if authority.destination_workspace_id != plan.destination_workspace_id:
        raise PermissionError("transfer authority destination does not match plan")
    expected_scope = (
        TransferAuthorityScope.EXPORT
        if plan.operation.value == "export"
        else TransferAuthorityScope.MATERIALIZE
    )
    if authority.scope is not expected_scope:
        raise PermissionError("transfer authority scope does not match transfer operation")
    validate_authenticated_transfer_authority(
        authority,
        authenticated_principal=principal,
        revocations=revocations,
    )

    if transaction.operation is not plan.operation:
        raise PermissionError("journal operation does not match transfer plan")
    if transaction.snapshot_id != plan.snapshot_id:
        raise PermissionError("journal snapshot does not match transfer plan")
    if transaction.source_workspace_id != plan.source_workspace_id:
        raise PermissionError("journal source does not match transfer plan")
    if transaction.destination_workspace_id != plan.destination_workspace_id:
        raise PermissionError("journal destination does not match transfer plan")
    if transaction.phase is not TransferJournalPhase.PREPARED:
        raise PermissionError("executor preflight requires a prepared transaction")

    if recovery is not None:
        if recovery.transaction_id != transaction.transaction_id:
            raise PermissionError("recovery plan transaction does not match journal")
        if recovery.snapshot_id != transaction.snapshot_id:
            raise PermissionError("recovery plan snapshot does not match journal")

    return ExecutorPreflightResult(
        principal=principal,
        authority=authority,
        transport=transport_gate,
        transaction_id=transaction.transaction_id,
        recovery=recovery,
    )
