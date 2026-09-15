"""Authenticated principal verification boundary.

This module contains only security contracts and immutable verification
 evidence. It does not implement signatures, certificates, key storage,
 transport, or trust decisions itself. A deployment must inject an audited
 verifier backed by authoritative trust and key admission.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    """Immutable evidence produced only after external authentication.

    The object is a provenance record, not an authority token. In particular,
    constructing this value directly must never be treated as authentication.
    """

    principal_id: str
    issuer_id: str
    node_id: str
    key_id: str
    key_fingerprint: str
    trust_root_id: str
    claims_digest: str

    def __post_init__(self) -> None:
        values = (
            self.principal_id,
            self.issuer_id,
            self.node_id,
            self.key_id,
            self.key_fingerprint,
            self.trust_root_id,
            self.claims_digest,
        )
        if any(not value for value in values):
            raise ValueError("authenticated principal evidence requires all identity fields")
        for field_name, value in (
            ("key fingerprint", self.key_fingerprint),
            ("claims digest", self.claims_digest),
        ):
            if len(value) != 64:
                raise ValueError(f"{field_name} requires a 64-character SHA-256 digest")
            try:
                int(value, 16)
            except ValueError as exc:
                raise ValueError(f"{field_name} requires hexadecimal SHA-256 encoding") from exc


@runtime_checkable
class TrustRootStore(Protocol):
    """Authoritative issuer trust-anchor lookup boundary."""

    def issuer_fingerprint(self, issuer_id: str) -> str | None: ...


@runtime_checkable
class PrincipalVerifier(Protocol):
    """Audited verification boundary for signed principal claims.

    Implementations must fail closed unless the issuer is trusted, the claimed
    node/key binding is admitted, the key is usable for verification, the
    signature is valid, and the signed claims bind all returned identity fields.
    """

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
    ) -> AuthenticatedPrincipal: ...
