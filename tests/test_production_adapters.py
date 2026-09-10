from fs_overlay.production_adapters import (
    AuthenticatedTransport,
    NodeAdmission,
    SecureKeyStore,
)


def test_production_adapter_contracts_are_importable() -> None:
    assert SecureKeyStore is not None
    assert AuthenticatedTransport is not None
    assert NodeAdmission is not None
