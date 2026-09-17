from __future__ import annotations

import socket
import stat

import pytest

from fs_overlay.genesis_service import GenesisService
from fs_overlay.identity import NodeIdentity
from fs_overlay.ipc import UnixSocketServer, UnixSocketTransport


def _service() -> GenesisService:
    return GenesisService(
        NodeIdentity("node-1", "fingerprint-1", 1),
        {"cpu": 2},
        admitted=True,
    )


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix-domain sockets unavailable")
def test_unix_socket_round_trip_and_restricted_mode(tmp_path):
    path = tmp_path / "fs.sock"
    with UnixSocketServer(_service(), path) as server:
        assert server.address == str(path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        response = UnixSocketTransport(path).request({"operation": "identity"})
        assert response["ok"] is True
        assert response["data"]["node_id"] == "node-1"
    assert not path.exists()


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix-domain sockets unavailable")
def test_unix_socket_does_not_replace_regular_file(tmp_path):
    path = tmp_path / "fs.sock"
    path.write_text("do not delete", encoding="utf-8")
    with pytest.raises(FileExistsError, match="not a socket"):
        UnixSocketServer(_service(), path).start()
    assert path.read_text(encoding="utf-8") == "do not delete"


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix-domain sockets unavailable")
def test_unix_socket_requires_absolute_path(tmp_path):
    with pytest.raises(ValueError, match="absolute"):
        UnixSocketServer(_service(), "relative.sock")
    with pytest.raises(ValueError, match="absolute"):
        UnixSocketTransport("relative.sock")


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix-domain sockets unavailable")
def test_unix_socket_rejects_overlong_path(tmp_path):
    path = "/" + ("x" * 108)
    with pytest.raises(ValueError, match="too long"):
        UnixSocketServer(_service(), path)


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix-domain sockets unavailable")
def test_unix_socket_does_not_grant_execution_authority(tmp_path):
    path = tmp_path / "fs.sock"
    service = GenesisService(
        NodeIdentity("node-1", "fingerprint-1", 1),
        {},
        admitted=False,
        executor=lambda argv: {"argv": argv},
    )
    with UnixSocketServer(service, path):
        response = UnixSocketTransport(path).request({"operation": "execute", "argv": ["id"]})
    assert response == {
        "data": {},
        "error": "node is not admitted",
        "ok": False,
        "operation": "execute",
    }
