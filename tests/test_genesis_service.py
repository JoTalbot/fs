from fs_overlay.genesis_runtime import build_local_service
from fs_overlay.identity import NodeIdentity


def make_service():
    identity = NodeIdentity.from_public_key("node-a", b"test-public-key")
    return build_local_service(identity, {"cpu": {"capacity": 4, "unit": "cores"}})


def test_bootstrap_boundary_is_not_ready_before_admission():
    service = make_service()
    assert service.handle({"operation": "ping"}).data["ready"] is False
    response = service.handle({"operation": "execute", "argv": ["python", "-c", "print('blocked')"]})
    assert not response.ok
    assert response.error == "node is not admitted"


def test_admission_is_bound_to_node_identity():
    service = make_service()
    bad = service.handle({"operation": "admit", "node_id": "other-node"})
    assert not bad.ok
    assert service.admitted is False


def test_identity_and_capability_inspection():
    service = make_service()
    identity = service.handle({"operation": "identity"})
    capabilities = service.handle({"operation": "capabilities"})
    assert identity.ok
    assert identity.data["node_id"] == "node-a"
    assert capabilities.data["cpu"]["capacity"] == 4


def test_admitted_service_can_execute_bounded_argv():
    service = make_service()
    assert service.handle({"operation": "admit", "node_id": "node-a"}).ok
    result = service.handle({"operation": "execute", "argv": ["python", "-c", "print('genesis-ok')"]})
    assert result.ok
    assert result.data["status"] == "succeeded"
    assert result.data["timed_out"] is False
    assert "genesis-ok" in result.data["stdout"]
