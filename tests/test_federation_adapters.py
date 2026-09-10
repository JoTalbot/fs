from fs_overlay.federation_adapters import FederationSigner, FederationTransport, KeyProvider


def test_contracts_are_runtime_importable() -> None:
    assert FederationSigner is not None
    assert FederationTransport is not None
    assert KeyProvider is not None
