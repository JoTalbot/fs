from __future__ import annotations

import os
import platform
import socket
import stat
import uuid

import pytest

import fs_overlay.ipc as ipc
from fs_overlay.genesis_service import GenesisService
from fs_overlay.identity import NodeIdentity
from fs_overlay.ipc import UnixSocketServer, UnixSocketTransport


def _service() -> GenesisService:
    return GenesisService(
        NodeIdentity("node-1", "fingerprint-1", 1),
        {"cpu": 2},
        admitted=True,
    )


def _socket_path(tmp_path):
    # macOS/BSD has a shorter sockaddr_un path budget than Linux. Keep the
    # functional test path short enough for Darwin while retaining pytest's
    # isolated tmp_path everywhere else.
    if platform.system() in {"Darwin", "FreeBSD", "OpenBSD", "NetBSD"}:
        return f"/tmp/fs-{os.getpid()}-{uuid.uuid4().hex}.sock"
    return tmp_path / "fs.sock"


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix-domain sockets unavailable")
def test_unix_socket_round_trip_and_restricted_mode(tmp_path):
    path = _socket_path(tmp_path)
    try:
        with UnixSocketServer(_service(), path) as server:
            assert server.address == str(path)
            assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
            response = UnixSocketTransport(path).request({"operation": "identity"})
            assert response["ok"] is True
            assert response["data"]["node_id"] == "node-1"
    finally:
        if isinstance(path, str):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
    assert not os.path.exists(path)


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix-domain sockets unavailable")
def test_unix_socket_does_not_replace_regular_file(tmp_path, monkeypatch):
    # pytest's macOS temp root can itself consume most of sockaddr_un's path
    # budget, so relax only the test seam to exercise the replacement guard.
    monkeypatch.setattr(ipc, "_UNIX_SOCKET_PATH_LIMIT", 4096)
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
    path = "/" + ("x" * 200)
    with pytest.raises(ValueError, match="too long"):
        UnixSocketServer(_service(), path)
    with pytest.raises(ValueError, match="too long"):
        UnixSocketTransport(path)


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix-domain sockets unavailable")
def test_unix_socket_does_not_grant_execution_authority(tmp_path):
    path = _socket_path(tmp_path)
    try:
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
    finally:
        if isinstance(path, str):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
