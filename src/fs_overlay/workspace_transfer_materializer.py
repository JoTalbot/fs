"""Non-destructive materializer admission boundary for workspace transfers.

The module intentionally performs no host filesystem mutation. A future
executor must enter through the unified security preflight and independently
revalidate every authority, identity, transport, transaction, and recovery
condition immediately before mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from .authority_policy import PolicyAuthorization
from .authority_revocation import AuthorityRevocationRegistry
from .identity_verification import AuthenticatedPrincipal, PrincipalVerifier, TrustRootStore
from .production_adapters import AuthenticatedTransport, KeyAdmission, NodeAdmission
from .workspace_migration import WorkspaceTransfer, WorkspaceTransferPlan
from .workspace_transfer_authority import TransferAuthority, TransferAuthorityScope
from .workspace_transfer_journal import TransferJournalEntry, TransferJournalPhase, WorkspaceTransferJournal
from .workspace_transfer_recovery import TransferRecoveryPlan


@dataclass(frozen=True, slots=True)
class MaterializationPreflight:
    """Evidence that a future materializer may enter its own mutation boundary."""

    transaction_id: str
    snapshot_id: str
    source_workspace_id: str
    destination_workspace_id: str
    operation: WorkspaceTransfer
    source_preserved: bool = True


class WorkspaceMaterializer(Protocol):
    """Interface for a future authority-bearing transfer executor.

    Implementations must revalidate preconditions immediately before mutation,
    journal each durable phase, preserve the source by default, and provide
    independently verified crash/rollback evidence. This protocol itself grants
    no filesystem access.
    """

    def prepare(self, plan: WorkspaceTransferPlan, authority: TransferAuthority, journal: WorkspaceTransferJournal) -> MaterializationPreflight: ...


def validate_materialization_preflight(
    plan: WorkspaceTransferPlan,
    authority: TransferAuthority,
    journal: WorkspaceTransferJournal,
    revocations: AuthorityRevocationRegistry | None = None,
) -> MaterializationPreflight:
    """Validate legacy plan/journal admission without host filesystem mutation.

    This compatibility boundary intentionally accepts no identity or transport
    evidence and therefore is not sufficient authorization for host mutation.
    Use ``validate_materialization_executor_preflight`` for any future executor.
    """
    if not plan.ready:
        raise ValueError("materialization requires a ready transfer plan")
    if not isinstance(authority, TransferAuthority):
        raise PermissionError("materialization requires an issued transfer authority")
    if authority.scope is not TransferAuthorityScope.MATERIALIZE:
        raise PermissionError("materialization requires materialize authority")
    if plan.operation is WorkspaceTransfer.EXPORT:
        raise ValueError("materialization requires an import or migration plan")
    if not plan.destination_path or not plan.destination_workspace_id:
        raise ValueError("materialization requires a destination workspace")
    if not authority.source_preserved:
        raise PermissionError("materialization authority must preserve the source")
    if (
        authority.snapshot_id != plan.snapshot_id
        or authority.source_workspace_id != plan.source_workspace_id
        or authority.destination_workspace_id != plan.destination_workspace_id
    ):
        raise PermissionError("authority does not match transfer plan")
    if revocations is not None:
        if not authority.authority_id:
            raise PermissionError("revocation check requires authority provenance")
        if revocations.is_revoked(authority.authority_id):
            raise PermissionError("transfer authority has been revoked")
    current = next(
        (entry for entry in reversed(list(journal.replay())) if entry.transaction_id == authority.transaction_id),
        None,
    )
    if current is None:
        raise ValueError("journal transaction does not exist")
    if current.operation is not plan.operation or current.snapshot_id != plan.snapshot_id:
        raise PermissionError("journal transaction does not match transfer plan")
    if current.source_workspace_id != plan.source_workspace_id or current.destination_workspace_id != plan.destination_workspace_id:
        raise PermissionError("journal workspaces do not match transfer plan")
    if current.phase not in {TransferJournalPhase.PREPARED, TransferJournalPhase.MATERIALIZING}:
        raise ValueError("transfer is not in a materializable journal state")
    return MaterializationPreflight(
        authority.transaction_id,
        plan.snapshot_id,
        plan.source_workspace_id,
        plan.destination_workspace_id,
        plan.operation,
        plan.source_preserved,
    )


def validate_materialization_executor_preflight(
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
) -> MaterializationPreflight:
    """Canonical admission facade for a future materialization executor."""
    from .executor_preflight import executor_preflight

    result = executor_preflight(
        plan,
        transaction=transaction,
        authority=authority,
        policy=policy,
        principal_verifier=principal_verifier,
        trust_roots=trust_roots,
        node_admission=node_admission,
        key_admission=key_admission,
        transport=transport,
        revocations=revocations,
        principal_id=principal_id,
        issuer_id=issuer_id,
        node_id=node_id,
        key_id=key_id,
        key_fingerprint=key_fingerprint,
        claims=claims,
        signature=signature,
        recovery=recovery,
    )
    return MaterializationPreflight(
        result.transaction_id,
        plan.snapshot_id,
        plan.source_workspace_id,
        plan.destination_workspace_id,
        plan.operation,
        plan.source_preserved,
    )
