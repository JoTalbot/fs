from fs_overlay.genesis_runtime import build_local_service
from fs_overlay.identity import NodeIdentity


def make_service(*, admitted=False):
    identity = NodeIdentity.from_public_key("node-a", b"test-public-key")
    return build_local_service(identity, {"cpu": {"capacity": 4, "unit": "cores"}}, admitted=admitted)


def test_bootstrap_boundary_is_not_ready_before_admission():
    service = make_service()
    assert service.handle({"operation": "ping"}).data["ready"] is False
    response = service.handle({"operation": "execute", "argv": ["python", "-c", "print('blocked')"]})
    assert not response.ok
    assert response.error == "node is not admitted"


def test_admission_cannot_be_granted_by_request_identity():
    service = make_service()
    response = service.handle({"operation": "admit", "node_id": "node-a"})
    assert not response.ok
    assert response.error == "unsupported operation: admit"
    assert service.admitted is False


def test_wrong_identity_cannot_change_admission_state():
    service = make_service()
    response = service.handle({"operation": "admit", "node_id": "other-node"})
    assert not response.ok
    assert service.admitted is False


def test_identity_and_capability_inspection():
    service = make_service()
    identity = service.handle({"operation": "identity"})
    capabilities = service.handle({"operation": "capabilities"})
    assert identity.ok
    assert identity.data["node_id"] == "node-a"
    assert capabilities.data["cpu"]["capacity"] == 4


def test_request_operation_must_be_a_string():
    service = make_service()
    response = service.handle({"operation": 1})
    assert not response.ok
    assert response.operation == ""
    assert response.error == "operation must be a string"


def test_request_rejects_unexpected_fields_before_dispatch():
    service = make_service()
    response = service.handle({"operation": "ping", "ready": True})
    assert not response.ok
    assert response.error == "unexpected request fields"


def test_execute_request_rejects_unexpected_fields_before_authority_gate():
    service = make_service()
    response = service.handle(
        {
            "operation": "execute",
            "argv": ["python", "-c", "print('blocked')"],
            "admitted": True,
        }
    )
    assert not response.ok
    assert response.error == "unexpected request fields"
    assert service.admitted is False


def test_explicitly_admitted_local_service_can_execute_bounded_argv():
    service = make_service(admitted=True)
    result = service.handle({"operation": "execute", "argv": ["python", "-c", "print('genesis-ok')"]})
    assert result.ok
    assert result.data["status"] == "succeeded"
    assert result.data["timed_out"] is False
    assert "genesis-ok" in result.data["stdout"]
