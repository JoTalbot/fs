import hashlib

import pytest

from fs_overlay.identity_preflight import identity_preflight
from fs_overlay.identity_verification import AuthenticatedPrincipal


FP = "a" * 64


class Roots:
    def issuer_fingerprint(self, issuer_id: str) -> str | None:
        return FP if issuer_id == "issuer-1" else None


class Verifier:
    def __init__(self):
        self.calls = 0

    def verify(self, **kwargs) -> AuthenticatedPrincipal:
        self.calls += 1
        return AuthenticatedPrincipal(
            kwargs["principal_id"], kwargs["issuer_id"], kwargs["node_id"],
            kwargs["key_id"], kwargs["key_fingerprint"], "root-1",
            hashlib.sha256(kwargs["claims"]).hexdigest(),
        )


class Nodes:
    def __init__(self, admitted: bool = True):
        self.admitted = admitted

    def is_admitted(self, node_id: str, public_key_fingerprint: str) -> bool:
        return self.admitted


class Keys:
    def __init__(self, admitted: bool = True, usable: bool = True):
        self.admitted = admitted
        self.usable = usable

    def is_key_admitted(self, node_id: str, key_id: str, fingerprint: str) -> bool:
        return self.admitted

    def can_verify(self, node_id: str, key_id: str) -> bool:
        return self.usable


@pytest.mark.parametrize("issuer", ["unknown", ""])
def test_preflight_rejects_untrusted_issuer_before_verifier(issuer: str):
    verifier = Verifier()
    with pytest.raises(PermissionError, match="issuer is not trusted"):
        identity_preflight(
            verifier,
            trust_roots=Roots(),
            node_admission=Nodes(), key_admission=Keys(),
            principal_id="principal-1", issuer_id=issuer, node_id="node-1",
            key_id="key-1", key_fingerprint=FP, claims=b"claims", signature=b"sig",
        )
    assert verifier.calls == 0


def test_preflight_composes_trust_verifier_and_admission():
    verifier = Verifier()
    principal = identity_preflight(
        verifier,
        trust_roots=Roots(),
        node_admission=Nodes(), key_admission=Keys(),
        principal_id="principal-1", issuer_id="issuer-1", node_id="node-1",
        key_id="key-1", key_fingerprint=FP, claims=b"claims", signature=b"sig",
    )
    assert principal.principal_id == "principal-1"
    assert verifier.calls == 1


@pytest.mark.parametrize(
    ("nodes", "keys", "message"),
    [(Nodes(False), Keys(), "node is not admitted"),
     (Nodes(), Keys(False), "key is not admitted"),
     (Nodes(), Keys(True, False), "not usable for verification")],
)
def test_preflight_fails_closed_on_admission(nodes, keys, message: str):
    with pytest.raises(PermissionError, match=message):
        identity_preflight(
            Verifier(), trust_roots=Roots(), node_admission=nodes, key_admission=keys,
            principal_id="principal-1", issuer_id="issuer-1", node_id="node-1",
            key_id="key-1", key_fingerprint=FP, claims=b"claims", signature=b"sig",
        )
