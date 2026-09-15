import pytest

from fs_overlay.identity_verification import AuthenticatedPrincipal
from fs_overlay.transport_gate import FailClosedTransportGate, TransportSecurityError


class FakeTransport:
    def __init__(self, *, peer="node-1", authenticated=True, frames=()):
        self.peer = peer
        self.authenticated = authenticated
        self.frames = list(frames)
        self.sent = []
        self.closed = False

    def authenticate(self, peer_node: str) -> None:
        self.peer = peer_node
        self.authenticated = True

    def send(self, peer_node: str, payload: bytes) -> None:
        assert peer_node == self.peer
        self.sent.append(payload)

    def receive(self) -> bytes | None:
        return self.frames.pop(0) if self.frames else None

    def peer_node(self) -> str | None:
        return self.peer

    def is_authenticated(self) -> bool:
        return self.authenticated

    def close(self) -> None:
        self.closed = True
        self.authenticated = False


class FailingTransport(FakeTransport):
    def __init__(self, *, send_error=False, receive_error=False):
        super().__init__()
        self.send_error = send_error
        self.receive_error = receive_error

    def send(self, peer_node: str, payload: bytes) -> None:
        if self.send_error:
            raise RuntimeError("provider send failure")
        super().send(peer_node, payload)

    def receive(self) -> bytes | None:
        if self.receive_error:
            raise RuntimeError("provider receive failure")
        return super().receive()


def principal() -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        "principal-1", "issuer-1", "node-1", "key-1", "a" * 64, "root-1", "b" * 64
    )


def frame(sequence: int, payload: bytes = b"payload") -> bytes:
    return sequence.to_bytes(8, "big") + payload


def test_send_binds_peer_and_adds_monotonic_sequence():
    transport = FakeTransport()
    gate = FailClosedTransportGate(transport, principal())
    gate.send(b"one")
    gate.send(b"two")
    assert transport.sent == [frame(1, b"one"), frame(2, b"two")]


def test_receive_accepts_next_sequence_only():
    transport = FakeTransport(frames=[frame(1, b"one"), frame(2, b"two")])
    gate = FailClosedTransportGate(transport, principal())
    assert gate.receive() == b"one"
    assert gate.receive() == b"two"


def test_receive_rejects_sequence_jump_and_closes():
    transport = FakeTransport(frames=[frame(2)])
    gate = FailClosedTransportGate(transport, principal())
    with pytest.raises(TransportSecurityError, match="replay or sequence"):
        gate.receive()
    assert transport.closed
    with pytest.raises(TransportSecurityError, match="session is closed"):
        gate.receive()


def test_receive_rejects_replay_after_a_valid_frame_and_closes():
    transport = FakeTransport(frames=[frame(1), frame(1)])
    gate = FailClosedTransportGate(transport, principal())
    assert gate.receive() == b"payload"
    with pytest.raises(TransportSecurityError, match="replay or sequence"):
        gate.receive()
    assert transport.closed
    with pytest.raises(TransportSecurityError, match="session is closed"):
        gate.receive()


def test_authentication_loss_fails_closed():
    transport = FakeTransport(authenticated=False)
    gate = FailClosedTransportGate(transport, principal())
    with pytest.raises(TransportSecurityError, match="not authenticated"):
        gate.send(b"blocked")
    assert transport.closed
    assert transport.sent == []


def test_peer_change_fails_closed():
    transport = FakeTransport()
    gate = FailClosedTransportGate(transport, principal())
    transport.peer = "node-evil"
    with pytest.raises(TransportSecurityError, match="does not match principal"):
        gate.send(b"blocked")
    assert transport.closed
    assert transport.sent == []


def test_provider_send_failure_closes_session():
    transport = FailingTransport(send_error=True)
    gate = FailClosedTransportGate(transport, principal())
    with pytest.raises(RuntimeError, match="provider send failure"):
        gate.send(b"blocked")
    assert transport.closed
    with pytest.raises(TransportSecurityError, match="session is closed"):
        gate.send(b"blocked")


def test_provider_receive_failure_closes_session():
    transport = FailingTransport(receive_error=True)
    gate = FailClosedTransportGate(transport, principal())
    with pytest.raises(RuntimeError, match="provider receive failure"):
        gate.receive()
    assert transport.closed
    with pytest.raises(TransportSecurityError, match="session is closed"):
        gate.receive()


def test_transport_state_provider_failure_fails_closed_and_closes():
    class BrokenStateTransport(FakeTransport):
        def is_authenticated(self) -> bool:
            raise RuntimeError("provider state failure")

    transport = BrokenStateTransport()
    gate = FailClosedTransportGate(transport, principal())
    with pytest.raises(TransportSecurityError, match="state could not be validated"):
        gate.validate_session()
    assert transport.closed


def test_malformed_frame_fails_closed():
    transport = FakeTransport(frames=[b"short"])
    gate = FailClosedTransportGate(transport, principal())
    with pytest.raises(TransportSecurityError, match="malformed"):
        gate.receive()
    assert transport.closed
