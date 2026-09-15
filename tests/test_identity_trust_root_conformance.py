import pytest

from fs_overlay.identity_verification import require_trusted_issuer
from fs_overlay.key_lifecycle import KeyLifecycle, KeyRecord
from fs_overlay.production_adapters import verify_and_validate_authenticated_principal
from tests.test_identity_verification import _admissions, _principal


def test_trust_root_rejects_unknown_issuer() -> None:
    class Roots:
        def issuer_fingerprint(self, issuer_id: str) -> str | None:
            return None

    with pytest.raises(PermissionError, match="issuer is not trusted"):
        require_trusted_issuer("issuer-1", trust_roots=Roots())


def test_trust_root_rejects_malformed_fingerprint() -> None:
    class Roots:
        def issuer_fingerprint(self, issuer_id: str) -> str | None:
            return "not-a-sha256"

    with pytest.raises(PermissionError, match="SHA-256"):
        require_trusted_issuer("issuer-1", trust_roots=Roots())


def test_trust_root_accepts_strict_sha256_fingerprint() -> None:
    class Roots:
        def issuer_fingerprint(self, issuer_id: str) -> str | None:
            return "A" * 64

    assert require_trusted_issuer("issuer-1", trust_roots=Roots()) == "A" * 64


def test_composed_identity_path_checks_trust_root_before_verifier() -> None:
    class Roots:
        def issuer_fingerprint(self, issuer_id: str) -> str | None:
            return None

    class Verifier:
        def verify(self, **kwargs):
            raise AssertionError("verifier must not run")

    nodes, keys = _admissions()
    with pytest.raises(PermissionError, match="issuer is not trusted"):
        verify_and_validate_authenticated_principal(
            Verifier(), principal_id="principal-1", issuer_id="issuer-1",
            node_id="node-1", key_id="key-1", key_fingerprint="a" * 64,
            claims=b"claims", signature=b"signature", trust_roots=Roots(),
            node_admission=nodes, key_admission=keys,
        )


def test_key_lifecycle_rotation_and_revocation_match_admission_semantics() -> None:
    lifecycle = KeyLifecycle([KeyRecord("k1", "a" * 64)])
    lifecycle.rotate(KeyRecord("k2", "b" * 64))
    assert not lifecycle.usable_for_signing("k1")
    assert lifecycle.usable_for_verification("k1")
    assert lifecycle.usable_for_signing("k2")
    lifecycle.revoke("k1")
    assert not lifecycle.usable_for_verification("k1")
    lifecycle.revoke("k2")
    assert not lifecycle.usable_for_signing("k2")
    assert not lifecycle.usable_for_verification("k2")
