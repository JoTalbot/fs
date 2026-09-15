import hashlib

import pytest

from fs_overlay.identity_verification import AuthenticatedPrincipal, PrincipalVerifier, TrustRootStore
from fs_overlay.production_adapters import (
    KeyAdmission,
    NodeAdmission,
    validate_authenticated_principal_admission,
    verify_and_validate_authenticated_principal,
)


def _principal() -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        principal_id="principal-1", issuer_id="issuer-1", node_id="node-1",
        key_id="key-1", key_fingerprint="a" * 64, trust_root_id="root-1", claims_digest="b" * 64,
    )


def _admissions(*, node_ok: bool = True, key_ok: bool = True, verify_ok: bool = True):
    class Nodes:
        def admit(self, node_id: str, public_key_fingerprint: str) -> bool: return True
        def revoke(self, node_id: str, reason: str = "") -> None: pass
        def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool: return node_ok

    class Keys:
        def admit_key(self, node_id: str, key_id: str, fingerprint: str) -> bool: return True
        def revoke_key(self, node_id: str, key_id: str, reason: str = "") -> None: pass
        def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool: return key_ok
        def can_sign(self, node_id: str, key_id: str) -> bool: return True
        def can_verify(self, node_id: str, key_id: str) -> bool: return verify_ok

    return Nodes(), Keys()


def test_authenticated_principal_evidence_requires_complete_identity() -> None:
    evidence = _principal()
    assert evidence.node_id == "node-1"
    assert evidence.key_fingerprint == "a" * 64


def test_authenticated_principal_rejects_malformed_fingerprints() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        AuthenticatedPrincipal("principal-1", "issuer-1", "node-1", "key-1", "short", "root-1", "b" * 64)


def test_authenticated_principal_rejects_non_hex_digests() -> None:
    with pytest.raises(ValueError, match="hexadecimal"):
        AuthenticatedPrincipal("principal-1", "issuer-1", "node-1", "key-1", "g" * 64, "root-1", "b" * 64)


def test_identity_security_contracts_are_runtime_structural() -> None:
    class Roots:
        def issuer_fingerprint(self, issuer_id: str) -> str | None:
            return "issuer-fp" if issuer_id == "issuer-1" else None

    class Verifier:
        def verify(self, *, principal_id: str, issuer_id: str, node_id: str, key_id: str,
                   key_fingerprint: str, claims: bytes, signature: bytes) -> AuthenticatedPrincipal:
            return AuthenticatedPrincipal(principal_id, issuer_id, node_id, key_id, key_fingerprint,
                                          "root-1", hashlib.sha256(claims).hexdigest())

    assert isinstance(Roots(), TrustRootStore)
    assert isinstance(Verifier(), PrincipalVerifier)


def test_principal_verification_boundary_does_not_store_secret_material() -> None:
    assert "secret" not in repr(_principal()).lower()


def test_authenticated_principal_admission_gate_accepts_consistent_evidence() -> None:
    nodes, keys = _admissions()
    validate_authenticated_principal_admission(_principal(), node_admission=nodes, key_admission=keys)


@pytest.mark.parametrize(
    ("node_ok", "key_ok", "verify_ok", "message"),
    [(False, True, True, "node is not admitted"),
     (True, False, True, "key is not admitted"),
     (True, True, False, "not usable for verification")],
)
def test_authenticated_principal_admission_gate_fails_closed(
    node_ok: bool, key_ok: bool, verify_ok: bool, message: str
) -> None:
    nodes, keys = _admissions(node_ok=node_ok, key_ok=key_ok, verify_ok=verify_ok)
    with pytest.raises(PermissionError, match=message):
        validate_authenticated_principal_admission(_principal(), node_admission=nodes, key_admission=keys)


def test_composed_verification_path_runs_admission_after_verifier() -> None:
    class Verifier:
        def verify(self, **kwargs) -> AuthenticatedPrincipal:
            return _principal()

    nodes, keys = _admissions()
    result = verify_and_validate_authenticated_principal(
        Verifier(), principal_id="principal-1", issuer_id="issuer-1", node_id="node-1",
        key_id="key-1", key_fingerprint="a" * 64, claims=b"claims", signature=b"signature",
        node_admission=nodes, key_admission=keys,
    )
    assert result == _principal()


def test_composed_verification_path_rejects_after_verifier_on_admission_failure() -> None:
    class Verifier:
        def verify(self, **kwargs) -> AuthenticatedPrincipal:
            return _principal()

    nodes, keys = _admissions(node_ok=False)
    with pytest.raises(PermissionError, match="node is not admitted"):
        verify_and_validate_authenticated_principal(
            Verifier(), principal_id="principal-1", issuer_id="issuer-1", node_id="node-1",
            key_id="key-1", key_fingerprint="a" * 64, claims=b"claims", signature=b"signature",
            node_admission=nodes, key_admission=keys,
        )


def test_admission_protocols_are_runtime_structural() -> None:
    nodes, keys = _admissions()
    assert isinstance(nodes, NodeAdmission)
    assert isinstance(keys, KeyAdmission)
