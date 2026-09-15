"""Production adapter contracts; security implementations remain injected."""
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol, runtime_checkable

from .identity_verification import (
    AuthenticatedPrincipal,
    PrincipalVerifier,
    TrustRootStore,
    require_trusted_issuer,
)
from .key_lifecycle import KeyLifecycle


@runtime_checkable
class SecureKeyStore(Protocol):
    def load(self, key_id: str) -> bytes: ...
    def store(self, key_id: str, key_material: bytes) -> None: ...
    def contains(self, key_id: str) -> bool: ...


@runtime_checkable
class AuthenticatedTransport(Protocol):
    def authenticate(self, peer_node: str) -> None: ...
    def send(self, peer_node: str, payload: bytes) -> None: ...
    def receive(self) -> bytes | None: ...
    def peer_node(self) -> str | None: ...
    def is_authenticated(self) -> bool: ...
    def close(self) -> None: ...


@runtime_checkable
class NodeAdmission(Protocol):
    def admit(self, node_id: str, public_key_fingerprint: str) -> bool: ...
    def revoke(self, node_id: str, reason: str = "") -> None: ...
    def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool: ...


@runtime_checkable
class KeyAdmission(Protocol):
    def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool: ...
    def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None: ...
    def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool: ...
    def can_sign(self, node_id: str, key_id: str) -> bool: ...
    def can_verify(self, node_id: str, key_id: str) -> bool: ...


class ReferenceKeyLifecycleAdmission:
    """Non-durable adapter that exposes ``KeyLifecycle`` as ``KeyAdmission``.

    This adapter exists only to qualify lifecycle semantics at the admission
    boundary. It is deliberately not a production authority: persistence,
    cross-process serialization, authenticated identity, and secure key storage
    remain deployment responsibilities supplied through injected adapters.
    """

    def __init__(self, lifecycle: KeyLifecycle):
        self._lifecycle = lifecycle
        self._node_by_key: dict[str, str] = {}

    def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool:
        if self._lifecycle.fingerprint_for(key_id) != fingerprint:
            return False
        bound = self._node_by_key.get(key_id)
        if bound is not None and bound != node_id:
            return False
        self._node_by_key[key_id] = node_id
        return True

    def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None:
        if self._node_by_key.get(key_id) == node_id:
            self._lifecycle.revoke(key_id)

    def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool:
        return (
            self._node_by_key.get(key_id) == node_id
            and self._lifecycle.fingerprint_for(key_id) == fingerprint
            and self._lifecycle.usable_for_verification(key_id)
        )

    def can_sign(self, node_id: str, key_id: str) -> bool:
        return self._node_by_key.get(key_id) == node_id and self._lifecycle.usable_for_signing(key_id)

    def can_verify(self, node_id: str, key_id: str) -> bool:
        return self._node_by_key.get(key_id) == node_id and self._lifecycle.usable_for_verification(key_id)



def validate_authenticated_principal_admission(
    principal: AuthenticatedPrincipal,
    *,
    node_admission: NodeAdmission,
    key_admission: KeyAdmission,
) -> None:
    if not node_admission.is_admitted(principal.node_id, principal.key_fingerprint):
        raise PermissionError("authenticated principal node is not admitted for its key fingerprint")
    if not key_admission.is_key_admitted(
        principal.node_id, principal.key_id, principal.key_fingerprint
    ):
        raise PermissionError("authenticated principal key is not admitted for its node")
    if not key_admission.can_verify(principal.node_id, principal.key_id):
        raise PermissionError("authenticated principal key is not usable for verification")


def verify_and_validate_authenticated_principal(
    verifier: PrincipalVerifier,
    *,
    principal_id: str,
    issuer_id: str,
    node_id: str,
    key_id: str,
    key_fingerprint: str,
    claims: bytes,
    signature: bytes,
    node_admission: NodeAdmission,
    key_admission: KeyAdmission,
    trust_roots: TrustRootStore,
) -> AuthenticatedPrincipal:
    """Verify identity through the mandatory authoritative trust-root gate.

    This is the production-facing composed identity path. An authoritative
    ``TrustRootStore`` is mandatory so callers cannot silently downgrade to a
    verifier-only path. The trust root is checked before cryptographic identity
    verification, followed by durable node/key admission. The store itself
    remains an injected security authority and this module never implements
    cryptography or persists key material.
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
        principal, node_admission=node_admission, key_admission=key_admission
    )
    return principal


@runtime_checkable
class DurableAdmissionCoordinator(Protocol):
    def acquire(self, resource_id: str) -> AbstractContextManager[None]: ...
