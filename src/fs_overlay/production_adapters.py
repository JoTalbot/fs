"""Production adapter contracts kept separate from reference implementations.

These protocols deliberately describe security-sensitive boundaries without
implementing cryptography, certificate validation, key storage, or network
policy. Deployments must supply audited implementations.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol, runtime_checkable

from .identity_verification import AuthenticatedPrincipal


@runtime_checkable
class SecureKeyStore(Protocol):
    """Opaque key-material storage boundary for a production signer."""

    def load(self, key_id: str) -> bytes: ...
    def store(self, key_id: str, key_material: bytes) -> None: ...
    def contains(self, key_id: str) -> bool: ...


@runtime_checkable
class AuthenticatedTransport(Protocol):
    """Authenticated/encrypted transport boundary for federation traffic."""

    def authenticate(self, peer_node: str) -> None: ...
    def send(self, peer_node: str, payload: bytes) -> None: ...
    def receive(self) -> bytes | None: ...
    def peer_node(self) -> str | None: ...
    def is_authenticated(self) -> bool: ...
    def close(self) -> None: ...


@runtime_checkable
class NodeAdmission(Protocol):
    """Authoritative node-admission boundary, separate from discovery."""

    def admit(self, node_id: str, public_key_fingerprint: str) -> bool: ...
    def revoke(self, node_id: str, reason: str = "") -> None: ...
    def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool: ...


@runtime_checkable
class KeyAdmission(Protocol):
    """Authoritative node/key binding and lifecycle admission boundary."""

    def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool: ...
    def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None: ...
    def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool: ...
    def can_sign(self, node_id: str, key_id: str) -> bool: ...
    def can_verify(self, node_id: str, key_id: str) -> bool: ...


def validate_authenticated_principal_admission(
    principal: AuthenticatedPrincipal,
    *,
    node_admission: NodeAdmission,
    key_admission: KeyAdmission,
) -> None:
    """Fail closed unless authenticated node/key evidence is admitted.

    This is a consistency gate, not authentication. The principal must come
    from an authoritative verifier. Issuer and trust-root validation remain
    verifier/trust-store responsibilities, and this function grants no host
    authority or filesystem mutation.
    """
    if not node_admission.is_admitted(principal.node_id, principal.key_fingerprint):
        raise PermissionError(
            "authenticated principal node is not admitted for its key fingerprint"
        )
    if not key_admission.is_key_admitted(
        principal.node_id, principal.key_id, principal.key_fingerprint
    ):
        raise PermissionError("authenticated principal key is not admitted for its node")
    if not key_admission.can_verify(principal.node_id, principal.key_id):
        raise PermissionError("authenticated principal key is not usable for verification")


@runtime_checkable
class TrustRootStore(Protocol):
    """Authoritative issuer trust-anchor lookup boundary."""

    def issuer_fingerprint(self, issuer_id: str) -> str | None: ...


@runtime_checkable
class PrincipalVerifier(Protocol):
    """Audited verification boundary for signed principal claims.

    Implementations must fail closed unless the issuer is trusted, the claimed
    node/key binding is admitted, the key is usable for verification, the
    signature is valid, and the signed claims bind all returned identity fields.
    """

    def verify(
        self,
        *,
        principal_id: str,
        issuer_id: str,
        node_id: str,
        key_id: str,
        key_fingerprint: str,
        claims: bytes,
        signature: bytes,
    ) -> AuthenticatedPrincipal: ...


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
) -> AuthenticatedPrincipal:
    """Verify signed identity and immediately enforce admission consistency.

    Cryptographic proof, trusted issuer/root validation, and claim binding are
    performed only by the injected audited verifier. This composition makes
    the authoritative node/key gate part of the normal verification path.
    """
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
    """Cross-process serialization boundary for durable admission state.

    Implementations must provide a real inter-process or transactional
    primitive. The reference ``DurableFederationState`` only serializes
    threads within one process and must not be treated as an implementation
    of this contract.
    """

    def acquire(self, resource_id: str) -> AbstractContextManager[None]: ...
