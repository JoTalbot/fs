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
from .recovery_preflight import RecoveryEvidenceVerifier, recovery_preflight
from .transport_gate import FailClosedTransportGate
from .workspace_migration import WorkspaceTransferPlan
from .workspace_transfer_authority import (
    TransferAuthority,
    TransferAuthorityScope,
    validate_authenticated_transfer_authority,
    validate_policy_bound_transfer_authority,
)
from .workspace_transfer_journal import TransferJournalEntry, TransferJournalPhase
from .workspace_transfer_recovery import TransferRecoveryEvidence, TransferRecoveryPlan


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
    recovery_evidence: TransferRecoveryEvidence | None = None,
    recovery_evidence_verifier: RecoveryEvidenceVerifier | None = None,
) -> ExecutorPreflightResult:
    """Require every executor security gate before any future mutation.

    A recovery path is accepted only when the raw recovery evidence is passed
    through ``recovery_preflight`` with an independent verifier. A caller cannot
    bypass that gate by constructing a structurally matching recovery plan.
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
    validate_policy_bound_transfer_authority(
        authority,
        policy=policy,
        authenticated_principal=principal,
    )
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

    verified_recovery = None
    if recovery is not None or recovery_evidence is not None:
        if recovery is None or recovery_evidence is None or recovery_evidence_verifier is None:
            raise PermissionError(
                "recovery requires evidence and an independent evidence verifier"
            )
        verified = recovery_preflight(
            transaction,
            recovery_evidence,
            evidence_verifier=recovery_evidence_verifier,
        )
        if (
            recovery.transaction_id != verified.plan.transaction_id
            or recovery.snapshot_id != verified.plan.snapshot_id
            or recovery.operation is not verified.plan.operation
            or recovery.decision is not verified.plan.decision
            or recovery.reason != verified.plan.reason
        ):
            raise PermissionError("recovery plan does not match independently verified evidence")
        verified_recovery = verified.plan

    return ExecutorPreflightResult(
        principal=principal,
        authority=authority,
        transport=transport_gate,
        transaction_id=transaction.transaction_id,
        recovery=verified_recovery,
    )
