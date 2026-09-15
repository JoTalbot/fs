import hashlib

import pytest

from fs_overlay.identity_verification import AuthenticatedPrincipal, PrincipalVerifier, TrustRootStore


def test_authenticated_principal_evidence_requires_complete_identity() -> None:
    evidence = AuthenticatedPrincipal(
        principal_id="principal-1",
        issuer_id="issuer-1",
        node_id="node-1",
        key_id="key-1",
        key_fingerprint="a" * 64,
        trust_root_id="root-1",
        claims_digest="b" * 64,
    )
    assert evidence.node_id == "node-1"
    assert evidence.key_fingerprint == "a" * 64


def test_authenticated_principal_rejects_malformed_fingerprints() -> None:
    with pytest.raises(ValueError, match="SHA-256 fingerprints"):
        AuthenticatedPrincipal(
            principal_id="principal-1",
            issuer_id="issuer-1",
            node_id="node-1",
            key_id="key-1",
            key_fingerprint="short",
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
    evidence = AuthenticatedPrincipal(
        principal_id="principal-1",
        issuer_id="issuer-1",
        node_id="node-1",
        key_id="key-1",
        key_fingerprint="a" * 64,
        trust_root_id="root-1",
        claims_digest=hashlib.sha256(b"claims").hexdigest(),
    )
    assert "secret" not in repr(evidence).lower()
