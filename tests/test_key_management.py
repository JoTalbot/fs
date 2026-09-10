from fs_overlay.key_management import FederationSigner, KeyProvider


def test_key_management_contracts_are_runtime_importable() -> None:
    assert FederationSigner is not None
    assert KeyProvider is not None
