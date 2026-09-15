import hashlib

import pytest

from fs_overlay.identity_verification import AuthenticatedPrincipal, PrincipalVerifier, TrustRootStore
from fs_overlay.production_adapters import (
    KeyAdmission,
    NodeAdmission,
    validate_authenticated_principal_admission,
)


def _principal() -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        principal_id="principal-1",
        issuer_id="issuer-1",
        node_id="node-1",
        key_id="key-1",
        key_fingerprint="a" * 64,
        trust_root_id="root-1",
        claims_digest="b" * 64,
    )


def test_authenticated_principal_evidence_requires_complete_identity() -> None:
    evidence = _principal()
    assert evidence.node_id == "node-1"
    assert evidence.key_fingerprint == "a" * 64


def test_authenticated_principal_rejects_malformed_fingerprints() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        AuthenticatedPrincipal(
            principal_id="principal-1",
            issuer_id="issuer-1",
            node_id="node-1",
            key_id="key-1",
            key_fingerprint="short",
            trust_root_id="root-1",
            claims_digest="b" * 64,
        )


def test_authenticated_principal_rejects_non_hex_digests() -> None:
    with pytest.raises(ValueError, match="hexadecimal"):
        AuthenticatedPrincipal(
            principal_id="principal-1",
            issuer_id="issuer-1",
            node_id="node-1",
            key_id="key-1",
            key_fingerprint="g" * 64,
            trust_root_id="root-1",
            claims_digest="b" * 64,
        )


def test_identity_security_contracts_are_runtime_structural() -> None:
    class Roots:
        def issuer_fingerprint(self, issuer_id: str) -> str | None:
            return "issuer-fp" if issuer_id == "issuer-1" else None

    class Verifier:
        def verify(
            self,
            *,
            principal_id: str,
            issuer_id: str,
            node_id: str,
            key_id: str,
            key_fingerprint: str,
            claims: bytes,
            signature: bytes,
        ) -> AuthenticatedPrincipal:
            return AuthenticatedPrincipal(
                principal_id=principal_id,
                issuer_id=issuer_id,
                node_id=node_id,
                key_id=key_id,
                key_fingerprint=key_fingerprint,
                trust_root_id="root-1",
                claims_digest=hashlib.sha256(claims).hexdigest(),
            )

    assert isinstance(Roots(), TrustRootStore)
    assert isinstance(Verifier(), PrincipalVerifier)


def test_principal_verification_boundary_does_not_store_secret_material() -> None:
    evidence = _principal()
    assert "secret" not in repr(evidence).lower()


def test_authenticated_principal_admission_gate_accepts_consistent_evidence() -> None:
    class Nodes:
        def admit(self, node_id: str, public_key_fingerprint: str) -> bool:
            return True

        def revoke(self, node_id: str, reason: str = "") -> None:
            raise AssertionError("not used")

        def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool:
            return node_id == "node-1" and public_key_fingerprint == "a" * 64

    class Keys:
        def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool:
            return True

        def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None:
            raise AssertionError("not used")

        def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool:
            return (node_id, key_id, fingerprint) == ("node-1", "key-1", "a" * 64)

        def can_sign(self, node_id: str, key_id: str) -> bool:
            return True

        def can_verify(self, node_id: str, key_id: str) -> bool:
            return (node_id, key_id) == ("node-1", "key-1")

    validate_authenticated_principal_admission(
        _principal(), node_admission=Nodes(), key_admission=Keys()
    )


def test_authenticated_principal_admission_gate_rejects_node_mismatch() -> None:
    class Nodes:
        def admit(self, node_id: str, public_key_fingerprint: str) -> bool:
            return True

        def revoke(self, node_id: str, reason: str = "") -> None:
            pass

        def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool:
            return False

    class Keys:
        def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool:
            return True

        def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None:
            pass

        def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool:
            return True

        def can_sign(self, node_id: str, key_id: str) -> bool:
            return True

        def can_verify(self, node_id: str, key_id: str) -> bool:
            return True

    with pytest.raises(PermissionError, match="node is not admitted"):
        validate_authenticated_principal_admission(
            _principal(), node_admission=Nodes(), key_admission=Keys()
        )


def test_authenticated_principal_admission_gate_rejects_key_binding_mismatch() -> None:
    class Nodes:
        def admit(self, node_id: str, public_key_fingerprint: str) -> bool:
            return True

        def revoke(self, node_id: str, reason: str = "") -> None:
            pass

        def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool:
            return True

    class Keys:
        def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool:
            return True

        def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None:
            pass

        def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool:
            return False

        def can_sign(self, node_id: str, key_id: str) -> bool:
            return True

        def can_verify(self, node_id: str, key_id: str) -> bool:
            return True

    with pytest.raises(PermissionError, match="key is not admitted"):
        validate_authenticated_principal_admission(
            _principal(), node_admission=Nodes(), key_admission=Keys()
        )


def test_authenticated_principal_admission_gate_rejects_unusable_key() -> None:
    class Nodes:
        def admit(self, node_id: str, public_key_fingerprint: str) -> bool:
            return True

        def revoke(self, node_id: str, reason: str = "") -> None:
            pass

        def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool:
            return True

    class Keys:
        def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool:
            return True

        def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None:
            pass

        def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool:
            return True

        def can_sign(self, node_id: str, key_id: str) -> bool:
            return True

        def can_verify(self, node_id: str, key_id: str) -> bool:
            return False

    with pytest.raises(PermissionError, match="not usable for verification"):
        validate_authenticated_principal_admission(
            _principal(), node_admission=Nodes(), key_admission=Keys()
        )


def test_admission_protocols_are_runtime_structural() -> None:
    class Nodes:
        def admit(self, node_id: str, public_key_fingerprint: str) -> bool:
            return True

        def revoke(self, node_id: str, reason: str = "") -> None:
            pass

        def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool:
            return True

    class Keys:
        def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool:
            return True

        def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None:
            pass

        def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool:
            return True

        def can_sign(self, node_id: str, key_id: str) -> bool:
            return True

        def can_verify(self, node_id: str, key_id: str) -> bool:
            return True

    assert isinstance(Nodes(), NodeAdmission)
    assert isinstance(Keys(), KeyAdmission)
