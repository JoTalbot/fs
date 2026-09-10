"""Reusable semantic qualification harness for FS production adapters.

The harness checks adapter contracts and fail-closed semantics. It deliberately
cannot certify cryptographic strength, secure storage, transport encryption,
distributed transactions, or operational security. Production adapters should
invoke this harness with their own authoritative implementations and add
implementation-specific tests beside them.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .production_adapters import (
    AuthenticatedTransport,
    DurableAdmissionCoordinator,
    KeyAdmission,
    NodeAdmission,
    SecureKeyStore,
)


class AdapterConformanceError(AssertionError):
    """Raised when an injected adapter violates the semantic contract."""


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AdapterConformanceError(message)


def run_adapter_conformance(
    *,
    key_store_factory: Callable[[], SecureKeyStore],
    transport_factory: Callable[[], AuthenticatedTransport],
    key_admission_factory: Callable[[], KeyAdmission],
    node_admission_factory: Callable[[], NodeAdmission],
    coordinator_factory: Callable[[], DurableAdmissionCoordinator],
) -> tuple[str, ...]:
    """Run the portable minimum contract against injected adapter instances.

    Factories must create fresh instances. The returned tuple contains stable
    check IDs suitable for CI logs and qualification reports.
    """

    checks: list[str] = []

    store: Any = key_store_factory()
    _check(isinstance(store, SecureKeyStore), "key store does not implement SecureKeyStore")
    _check(not store.contains("k1"), "new key store must not contain an unknown key")
    try:
        store.store("", b"qualification-key")
    except (ValueError, TypeError):
        pass
    else:
        raise AdapterConformanceError("empty key id must be rejected")
    store.store("k1", b"qualification-key")
    _check(store.contains("k1"), "stored key must be addressable")
    _check(store.load("k1") == b"qualification-key", "stored key must round-trip")
    try:
        store.store("k-empty", b"")
    except (ValueError, TypeError):
        pass
    else:
        raise AdapterConformanceError("empty key material must be rejected")
    checks.append("secure-key-store")

    transport: Any = transport_factory()
    _check(isinstance(transport, AuthenticatedTransport), "transport does not implement AuthenticatedTransport")
    try:
        transport.send("node-a", b"qualification")
    except (PermissionError, RuntimeError):
        pass
    else:
        raise AdapterConformanceError("unauthenticated transport send must be rejected")
    transport.authenticate("node-a")
    _check(transport.is_authenticated(), "authenticated transport must expose authenticated state")
    _check(transport.peer_node() == "node-a", "authenticated peer identity must be observable")
    try:
        transport.send("node-b", b"qualification")
    except (PermissionError, RuntimeError):
        pass
    else:
        raise AdapterConformanceError("transport must reject sends to an unauthenticated peer")
    transport.send("node-a", b"qualification")
    _check(transport.receive() == b"qualification", "authenticated payload must be receivable")
    transport.close()
    _check(not transport.is_authenticated(), "closed transport must lose authentication")
    checks.append("authenticated-transport")

    keys: Any = key_admission_factory()
    _check(isinstance(keys, KeyAdmission), "key admission does not implement KeyAdmission")
    _check(not keys.admit_key("", "k1", "fp-a"), "empty node id must be rejected by key admission")
    _check(not keys.admit_key("node-a", "", "fp-a"), "empty key id must be rejected by key admission")
    _check(not keys.admit_key("node-a", "k1", ""), "empty key fingerprint must be rejected")
    _check(keys.admit_key("node-a", "k1", "fp-a"), "initial key admission must succeed")
    _check(keys.is_key_admitted("node-a", "k1", "fp-a"), "admitted key must be observable")
    _check(not keys.admit_key("node-a", "k1", "fp-b"), "key fingerprint change must be rejected")
    _check(keys.can_sign("node-a", "k1"), "admitted key must be sign-capable")
    _check(keys.can_verify("node-a", "k1"), "admitted key must be verify-capable")
    keys.revoke_key("node-a", "k1", "qualification")
    _check(not keys.can_sign("node-a", "k1"), "revoked key must not sign")
    _check(not keys.can_verify("node-a", "k1"), "revoked key must not verify")
    checks.append("key-admission")

    nodes: Any = node_admission_factory()
    _check(isinstance(nodes, NodeAdmission), "node admission does not implement NodeAdmission")
    _check(not nodes.admit("", "fp-a"), "empty node id must be rejected")
    _check(not nodes.admit("node-a", ""), "empty node fingerprint must be rejected")
    _check(nodes.admit("node-a", "fp-a"), "initial node admission must succeed")
    _check(nodes.is_admitted("node-a", "fp-a"), "admitted node must be observable")
    _check(not nodes.admit("node-a", "fp-b"), "node fingerprint change must be rejected")
    nodes.revoke("node-a", "qualification")
    _check(not nodes.is_admitted("node-a", "fp-a"), "revoked node must not remain admitted")
    checks.append("node-admission")

    coordinator: Any = coordinator_factory()
    _check(isinstance(coordinator, DurableAdmissionCoordinator), "coordinator does not implement DurableAdmissionCoordinator")
    resource = "qualification-resource"
    with coordinator.acquire(resource):
        pass
    checks.append("durable-coordinator-release")

    return tuple(checks)
