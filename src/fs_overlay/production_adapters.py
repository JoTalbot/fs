"""Production adapter contracts kept separate from reference implementations.

These protocols deliberately describe security-sensitive boundaries without
implementing cryptography, certificate validation, key storage, or network
policy. Deployments must supply audited implementations.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol, runtime_checkable


class SecureKeyStore(Protocol):
    """Opaque key-material storage boundary for a production signer."""

    def load(self, key_id: str) -> bytes: ...

    def store(self, key_id: str, key_material: bytes) -> None: ...

    def contains(self, key_id: str) -> bool: ...


class AuthenticatedTransport(Protocol):
    """Authenticated/encrypted transport boundary for federation traffic."""

    def send(self, peer_node: str, payload: bytes) -> None: ...
    def receive(self) -> bytes | None: ...
    def peer_node(self) -> str | None: ...
    def is_authenticated(self) -> bool: ...
    def close(self) -> None: ...


class NodeAdmission(Protocol):
    """Authoritative node-admission boundary, separate from discovery."""

    def admit(self, node_id: str, public_key_fingerprint: str) -> bool: ...

    def revoke(self, node_id: str, reason: str = "") -> None: ...

    def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool: ...


class KeyAdmission(Protocol):
    """Authoritative node/key binding and lifecycle admission boundary."""

    def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool: ...

    def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None: ...

    def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool: ...

    def can_sign(self, node_id: str, key_id: str) -> bool: ...

    def can_verify(self, node_id: str, key_id: str) -> bool: ...


@runtime_checkable
class DurableAdmissionCoordinator(Protocol):
    """Cross-process serialization boundary for durable admission state.

    Implementations must provide a real inter-process or transactional
    primitive. The reference ``DurableFederationState`` only serializes
    threads within one process and must not be treated as an implementation
    of this contract.
    """

    def acquire(self, resource_id: str) -> AbstractContextManager[None]: ...
