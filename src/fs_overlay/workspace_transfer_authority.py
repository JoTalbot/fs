"""Explicit authority boundary for future workspace transfer materialization.

This module is deliberately contract-only: creating an authority token requires
an already verified transfer plan and an explicit caller decision. The token is
not inferred from filesystem capabilities and performs no filesystem mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .workspace_migration import WorkspaceTransferPlan


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
