"""Fail-closed policy boundary for explicit workspace transfer authority.

This module binds an authority grant to an authenticated-principal *claim*
and immutable policy constraints. It deliberately does not implement
cryptographic authentication, revocation storage, or filesystem mutation.
Those mechanisms belong to the future control plane/security provider.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthorityConstraints:
    """Immutable bounds that a future executor must not widen."""

    workspace_id: str
    snapshot_id: str
    allow_source_delete: bool = False
    allow_network: bool = False

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise ValueError("authority constraint requires workspace_id")
        if not self.snapshot_id:
            raise ValueError("authority constraint requires snapshot_id")
        if self.allow_source_delete:
            raise PermissionError("source deletion is not permitted by the transfer safety policy")


@dataclass(frozen=True, slots=True)
class AuthorityPrincipal:
    """Named principal claim supplied by an external authenticated control plane."""

    principal_id: str
    issuer_id: str

    def __post_init__(self) -> None:
        if not self.principal_id or not self.issuer_id:
            raise ValueError("authority principal requires principal and issuer identity")


@dataclass(frozen=True, slots=True)
class PolicyAuthorization:
    """Policy decision that can be consumed by authority issuance."""

    principal: AuthorityPrincipal
    constraints: AuthorityConstraints
    approved: bool

    def require_approved(self) -> None:
        if not self.approved:
            raise PermissionError("policy did not explicitly authorize transfer")


def validate_policy_authorization(
    authorization: PolicyAuthorization,
    *,
    workspace_id: str,
    snapshot_id: str,
) -> None:
    """Require exact policy identity binding; never infer approval from capability."""
    authorization.require_approved()
    if authorization.constraints.workspace_id != workspace_id:
        raise PermissionError("policy workspace constraint does not match transfer")
    if authorization.constraints.snapshot_id != snapshot_id:
        raise PermissionError("policy snapshot constraint does not match transfer")
