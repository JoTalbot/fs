from contextlib import nullcontext

from fs_overlay.production_adapters import (
    AuthenticatedTransport,
    DurableAdmissionCoordinator,
    KeyAdmission,
    NodeAdmission,
    SecureKeyStore,
)


def test_production_adapter_contracts_are_importable() -> None:
    assert SecureKeyStore is not None
    assert AuthenticatedTransport is not None
    assert NodeAdmission is not None
    assert KeyAdmission is not None
    assert DurableAdmissionCoordinator is not None


def test_durable_admission_coordinator_contract_shape() -> None:
    class Coordinator:
        def acquire(self, resource_id: str):
            assert resource_id == "federation-events"
            return nullcontext()

    coordinator = Coordinator()
    assert isinstance(coordinator, DurableAdmissionCoordinator)
    with coordinator.acquire("federation-events"):
        pass
