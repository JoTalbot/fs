import time

import pytest

from fs_overlay.genesis_runtime import build_local_service
from fs_overlay.genesis_server import GenesisServer
from fs_overlay.identity import NodeIdentity
from fs_overlay.transport import LocalhostTransport


def make_service():
    identity = NodeIdentity.from_public_key("node-server", b"server-key")
    return build_local_service(identity, {"cpu": {"capacity": 2, "unit": "cores"}})


def wait_for_port(server: GenesisServer) -> tuple[str, int]:
    for _ in range(100):
        address = server.address
        if address is not None:
            return address
        time.sleep(0.005)
    raise AssertionError("server did not publish an address")


def test_genesis_server_is_loopback_only():
    with pytest.raises(ValueError):
        GenesisServer(make_service(), host="0.0.0.0")


def test_genesis_server_round_trip_and_admission_gate():
    service = make_service()
    with GenesisServer(service) as server:
        host, port = wait_for_port(server)
        assert host == "127.0.0.1"

        transport = LocalhostTransport()
        before = transport.request(port, {"operation": "ping"})
        assert before["ok"]
        assert before["data"]["ready"] is False

        blocked = transport.request(
            port,
            {"operation": "execute", "argv": ["python", "-c", "print('blocked')"]},
        )
        assert not blocked["ok"]
        assert blocked["error"] == "node is not admitted"

        admitted = transport.request(
            port,
            {"operation": "admit", "node_id": "node-server"},
        )
        assert admitted["ok"]

        result = transport.request(
            port,
            {"operation": "execute", "argv": ["python", "-c", "print('server-ok')"]},
        )
        assert result["ok"]
        assert result["data"]["status"] == "succeeded"
        assert "server-ok" in result["data"]["stdout"]
