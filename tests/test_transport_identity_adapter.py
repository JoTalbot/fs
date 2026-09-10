import socket
import threading

import pytest

from fs_overlay.adapter import NativeProcessAdapter
from fs_overlay.identity import NodeIdentity
from fs_overlay.transport import LocalhostTransport, recv_message, send_message


def test_node_identity_is_deterministic() -> None:
    first = NodeIdentity.from_public_key("node-a", b"key")
    second = NodeIdentity.from_public_key("node-a", b"key")
    assert first == second
    assert first.validate() == ()


def test_localhost_transport_rejects_non_loopback() -> None:
    with pytest.raises(ValueError):
        LocalhostTransport("192.0.2.1")


def test_framed_localhost_request() -> None:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    def serve() -> None:
        with listener:
            conn, _ = listener.accept()
            with conn:
                request = recv_message(conn)
                send_message(conn, {"ok": request["operation"] == "ping"})

    thread = threading.Thread(target=serve)
    thread.start()
    response = LocalhostTransport().request(port, {"operation": "ping"})
    thread.join(timeout=2)
    assert response == {"ok": True}


def test_native_adapter_requires_admission() -> None:
    adapter = NativeProcessAdapter()
    result = adapter.execute(("python", "-c", "print('fs-ok')"))
    assert result.status == "rejected"


def test_native_adapter_uses_argv_without_shell() -> None:
    adapter = NativeProcessAdapter()
    result = adapter.execute(("python", "-c", "print('fs-ok')"), admitted=True)
    assert result.status == "succeeded"
    assert "fs-ok" in result.stdout
