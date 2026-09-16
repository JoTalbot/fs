from contextlib import nullcontext

from fs_overlay.key_lifecycle import KeyLifecycle, KeyRecord
from fs_overlay.production_adapters import (
    AuthenticatedTransport,
    DurableAdmissionCoordinator,
    KeyAdmission,
    NodeAdmission,
    ReferenceKeyLifecycleAdmission,
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


def test_reference_key_admission_cannot_reactivate_retired_or_revoked_key() -> None:
    lifecycle = KeyLifecycle([KeyRecord("key-1", "fp-1")])
    admission = ReferenceKeyLifecycleAdmission(lifecycle)
    assert admission.admit_key("node-1", "key-1", "fp-1")

    admission.retire_key("node-1", "key-1")
    assert not admission.can_sign("node-1", "key-1")
    assert admission.can_verify("node-1", "key-1")
    assert not admission.admit_key("node-1", "key-1", "fp-1")

    admission.revoke_key("node-1", "key-1")
    assert not admission.can_sign("node-1", "key-1")
    assert not admission.can_verify("node-1", "key-1")
    assert not admission.admit_key("node-1", "key-1", "fp-1")


def test_reference_key_admission_rejects_re_admission_after_rotation() -> None:
    lifecycle = KeyLifecycle([KeyRecord("key-1", "fp-1")])
    admission = ReferenceKeyLifecycleAdmission(lifecycle)
    assert admission.admit_key("node-1", "key-1", "fp-1")

    lifecycle.rotate(KeyRecord("key-2", "fp-2"))

    assert not admission.can_sign("node-1", "key-1")
    assert admission.can_verify("node-1", "key-1")
    assert not admission.admit_key("node-2", "key-1", "fp-1")
    assert admission.admit_key("node-2", "key-2", "fp-2")
