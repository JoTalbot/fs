"""Fail-closed production identity preflight composition.

This module composes the authoritative trust-root, cryptographic verifier,
node admission, and key admission boundaries without granting host authority.
"""
from __future__ import annotations

from .identity_verification import (
    AuthenticatedPrincipal,
    PrincipalVerifier,
    TrustRootStore,
    require_trusted_issuer,
)
from .production_adapters import KeyAdmission, NodeAdmission, validate_authenticated_principal_admission


def identity_preflight(
    verifier: PrincipalVerifier,
    *,
    trust_roots: TrustRootStore,
    node_admission: NodeAdmission,
    key_admission: KeyAdmission,
    principal_id: str,
    issuer_id: str,
    node_id: str,
    key_id: str,
    key_fingerprint: str,
    claims: bytes,
    signature: bytes,
) -> AuthenticatedPrincipal:
    """Authenticate and admit an identity through every required gate.

    Trust-root admission is mandatory and runs before the verifier. The
    resulting principal is then checked against the authoritative node/key
    admission registries, including verification usability. Any failed gate
    raises ``PermissionError`` and no host filesystem authority is implied.
    """
    require_trusted_issuer(issuer_id, trust_roots=trust_roots)
    principal = verifier.verify(
        principal_id=principal_id,
        issuer_id=issuer_id,
        node_id=node_id,
        key_id=key_id,
        key_fingerprint=key_fingerprint,
        claims=claims,
        signature=signature,
    )
    validate_authenticated_principal_admission(
        principal,
        node_admission=node_admission,
        key_admission=key_admission,
    )
    return principal
