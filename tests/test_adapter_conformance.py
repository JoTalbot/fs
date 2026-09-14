from __future__ import annotations

from contextlib import contextmanager

import pytest

from fs_overlay.adapter_conformance import AdapterConformanceError, run_adapter_conformance
from fs_overlay.durable_coordination import FileAdmissionCoordinator
from fs_overlay.production_adapters import (
    AuthenticatedTransport,
    DurableAdmissionCoordinator,
    KeyAdmission,
    NodeAdmission,
    SecureKeyStore,
)


class MemoryKeyStore:
    def __init__(self) -> None:
        self._keys: dict[str, bytes] = {}

    def load(self, key_id: str) -> bytes:
        return self._keys[key_id]

    def store(self, key_id: str, key_material: bytes) -> None:
        if not key_id or not key_material:
            raise ValueError("key material must be non-empty")
        self._keys[key_id] = bytes(key_material)

    def contains(self, key_id: str) -> bool:
        return key_id in self._keys


class MemoryTransport:
    def __init__(self) -> None:
        self._peer: str | None = None
        self._authenticated = False
        self._messages: list[bytes] = []
        self.closed = False

    def authenticate(self, peer_node: str) -> None:
        if not peer_node:
            raise ValueError("peer identity is required")
        self._peer = peer_node
        self._authenticated = True

    def send(self, peer_node: str, payload: bytes) -> None:
        if not self._authenticated or peer_node != self._peer:
            raise PermissionError("transport is not authenticated for this peer")
        self._messages.append(bytes(payload))

    def receive(self) -> bytes | None:
        return self._messages.pop(0) if self._messages else None

    def peer_node(self) -> str | None:
        return self._peer

    def is_authenticated(self) -> bool:
        return self._authenticated and not self.closed

    def close(self) -> None:
        self.closed = True
        self._authenticated = False


class MemoryKeyAdmission:
    def __init__(self) -> None:
        self._keys: dict[tuple[str, str], str] = {}
        self._revoked: set[tuple[str, str]] = set()

    def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool:
        if not node_id or not key_id or not fingerprint:
            return False
        key = (node_id, key_id)
        if key in self._revoked:
            return False
        previous = self._keys.get(key)
        if previous is not None and previous != fingerprint:
            return False
        self._keys[key] = fingerprint
        return True

    def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None:
        key = (node_id, key_id)
        self._keys.pop(key, None)
        self._revoked.add(key)

    def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool:
        return (node_id, key_id) not in self._revoked and self._keys.get((node_id, key_id)) == fingerprint

    def can_sign(self, node_id: str, key_id: str) -> bool:
        return (node_id, key_id) in self._keys and (node_id, key_id) not in self._revoked

    def can_verify(self, node_id: str, key_id: str) -> bool:
        return self.can_sign(node_id, key_id)


class MemoryCoordinator:
    def __init__(self) -> None:
        self.resources: list[str] = []

    @contextmanager
    def acquire(self, resource_id: str):
        if not resource_id:
            raise ValueError("resource id is required")
        self.resources.append(resource_id)
        try:
            yield
        finally:
            self.resources.remove(resource_id)


class NodeAllowlist:
    def __init__(self) -> None:
        self.nodes: dict[str, str] = {}
        self.revoked: set[str] = set()

    def admit(self, node_id: str, public_key_fingerprint: str) -> bool:
        if not node_id or not public_key_fingerprint or node_id in self.revoked:
            return False
        previous = self.nodes.get(node_id)
        if previous is not None and previous != public_key_fingerprint:
            return False
        self.nodes[node_id] = public_key_fingerprint
        return True

    def revoke(self, node_id: str, reason: str = "") -> None:
        self.nodes.pop(node_id, None)
        self.revoked.add(node_id)

    def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool:
        return node_id not in self.revoked and self.nodes.get(node_id) == public_key_fingerprint


def test_secure_key_store_contract_and_fail_closed_empty_key() -> None:
    store = MemoryKeyStore()
    assert isinstance(store, SecureKeyStore)
    assert not store.contains("k1")
    try:
        store.store("", b"secret")
    except ValueError:
        pass
    else:
        raise AssertionError("empty key id must be rejected")
    store.store("k1", b"secret")
    assert store.contains("k1")
    assert store.load("k1") == b"secret"
    try:
        store.store("k2", b"")
    except ValueError:
        pass
    else:
        raise AssertionError("empty key material must be rejected")


def test_authenticated_transport_requires_authenticated_peer() -> None:
    transport = MemoryTransport()
    assert isinstance(transport, AuthenticatedTransport)
    try:
        transport.send("node-a", b"message")
    except PermissionError:
        pass
    else:
        raise AssertionError("unauthenticated transport must reject sends")
    transport.authenticate("node-a")
    assert transport.is_authenticated()
    assert transport.peer_node() == "node-a"
    with pytest.raises(PermissionError):
        transport.send("node-b", b"message")
    transport.send("node-a", b"message")
    assert transport.receive() == b"message"
    transport.close()
    assert not transport.is_authenticated()


def test_key_admission_rejects_fingerprint_change_and_revocation() -> None:
    admission = MemoryKeyAdmission()
    assert isinstance(admission, KeyAdmission)
    assert not admission.admit_key("", "k1", "fp-a")
    assert not admission.admit_key("node-a", "", "fp-a")
    assert not admission.admit_key("node-a", "k1", "")
    assert admission.admit_key("node-a", "k1", "fp-a")
    assert admission.is_key_admitted("node-a", "k1", "fp-a")
    assert not admission.admit_key("node-a", "k1", "fp-b")
    assert not admission.is_key_admitted("node-a", "k1", "fp-b")
    assert admission.can_sign("node-a", "k1")
    assert admission.can_verify("node-a", "k1")
    admission.revoke_key("node-a", "k1", "test")
    assert not admission.can_sign("node-a", "k1")
    assert not admission.can_verify("node-a", "k1")


def test_node_admission_contract_is_distinct_from_key_admission() -> None:
    admission = NodeAllowlist()
    assert isinstance(admission, NodeAdmission)
    assert not admission.admit("", "fp-a")
    assert not admission.admit("node-a", "")
    assert admission.admit("node-a", "fp-a")
    assert admission.is_admitted("node-a", "fp-a")
    assert not admission.admit("node-a", "fp-b")
    admission.revoke("node-a", "test")
    assert not admission.is_admitted("node-a", "fp-a")


def test_durable_coordinator_contract_requires_release() -> None:
    coordinator = MemoryCoordinator()
    assert isinstance(coordinator, DurableAdmissionCoordinator)
    with coordinator.acquire("federation-events"):
        assert coordinator.resources == ["federation-events"]
    assert coordinator.resources == []


def test_reusable_adapter_qualification_harness() -> None:
    checks = run_adapter_conformance(
        key_store_factory=MemoryKeyStore,
        transport_factory=MemoryTransport,
        key_admission_factory=MemoryKeyAdmission,
        node_admission_factory=NodeAllowlist,
        coordinator_factory=MemoryCoordinator,
    )
    assert checks == (
        "secure-key-store",
        "authenticated-transport",
        "key-admission",
        "node-admission",
        "durable-coordinator-release",
    )


def test_file_admission_coordinator_qualifies(tmp_path) -> None:
    checks = run_adapter_conformance(
        key_store_factory=MemoryKeyStore,
        transport_factory=MemoryTransport,
        key_admission_factory=MemoryKeyAdmission,
        node_admission_factory=NodeAllowlist,
        coordinator_factory=lambda: FileAdmissionCoordinator(tmp_path / "qualification-locks", timeout=0.2),
    )
    assert checks[-1] == "durable-coordinator-release"


class PermissiveKeyStore(MemoryKeyStore):
    def store(self, key_id: str, key_material: bytes) -> None:
        if not key_id:
            raise ValueError("key id must be non-empty")
        self._keys[key_id] = bytes(key_material)


class PermissiveTransport(MemoryTransport):
    def send(self, peer_node: str, payload: bytes) -> None:
        self._messages.append(bytes(payload))


@pytest.mark.parametrize(
    ("factory_kwargs", "expected"),
    [
        ({"key_store_factory": PermissiveKeyStore}, "empty key material must be rejected"),
        ({"transport_factory": PermissiveTransport}, "unauthenticated transport send must be rejected"),
    ],
)
def test_reusable_harness_rejects_fail_open_adapter(
    factory_kwargs: dict[str, object], expected: str
) -> None:
    factories = {
        "key_store_factory": MemoryKeyStore,
        "transport_factory": MemoryTransport,
        "key_admission_factory": MemoryKeyAdmission,
        "node_admission_factory": NodeAllowlist,
        "coordinator_factory": MemoryCoordinator,
    }
    factories.update(factory_kwargs)
    with pytest.raises(AdapterConformanceError, match=expected):
        run_adapter_conformance(**factories)
