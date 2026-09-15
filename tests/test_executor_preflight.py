from dataclasses import replace
from pathlib import Path

import pytest

from fs_overlay.authority_policy import AuthorityConstraints, AuthorityPrincipal, PolicyAuthorization
from fs_overlay.authority_revocation import AuthorityRevocationRegistry
from fs_overlay.executor_preflight import executor_preflight
from fs_overlay.identity_verification import AuthenticatedPrincipal
from fs_overlay.workspace_migration import WorkspaceTransfer, WorkspaceTransferPlan
from fs_overlay.workspace_transfer_authority import (
    TransferAuthorityScope,
    grant_authenticated_policy_bound_transfer_authority,
)
from fs_overlay.workspace_transfer_journal import TransferJournalEntry, TransferJournalPhase


FINGERPRINT = "a" * 64
CLAIMS_DIGEST = "b" * 64


class TrustRoots:
    def issuer_fingerprint(self, issuer_id):
        return FINGERPRINT if issuer_id == "issuer-1" else None


class Verifier:
    def __init__(self):
        self.calls = 0

    def verify(self, **kwargs):
        self.calls += 1
        return AuthenticatedPrincipal(
            kwargs["principal_id"], kwargs["issuer_id"], kwargs["node_id"],
            kwargs["key_id"], kwargs["key_fingerprint"], "root-1", CLAIMS_DIGEST,
        )


class Nodes:
    def is_admitted(self, node_id, fingerprint):
        return node_id == "node-1" and fingerprint == FINGERPRINT


class Keys:
    def is_key_admitted(self, node_id, key_id, fingerprint):
        return (node_id, key_id, fingerprint) == ("node-1", "key-1", FINGERPRINT)

    def can_verify(self, node_id, key_id):
        return (node_id, key_id) == ("node-1", "key-1")

    def can_sign(self, node_id, key_id):
        return self.can_verify(node_id, key_id)

    def admit_key(self, *args, **kwargs):
        return True

    def revoke_key(self, *args, **kwargs):
        return None


class Transport:
    def __init__(self, peer="node-1", authenticated=True):
        self.peer = peer
        self.authenticated = authenticated
        self.closed = False

    def authenticate(self, peer_node):
        self.peer = peer_node
        self.authenticated = True

    def send(self, peer_node, payload):
        assert peer_node == self.peer

    def receive(self):
        return None

    def peer_node(self):
        return self.peer

    def is_authenticated(self):
        return self.authenticated

    def close(self):
        self.closed = True


def plan():
    return WorkspaceTransferPlan(
        WorkspaceTransfer.MIGRATE,
        "snapshot-1",
        "source-1",
        "dest-1",
        Path("/source"),
        Path("/dest"),
    )


def policy():
    return PolicyAuthorization(
        AuthorityPrincipal("principal-1", "issuer-1"),
        AuthorityConstraints("dest-1", "snapshot-1"),
        True,
    )


def principal():
    return AuthenticatedPrincipal(
        "principal-1", "issuer-1", "node-1", "key-1", FINGERPRINT, "root-1", CLAIMS_DIGEST,
    )


def authority():
    return grant_authenticated_policy_bound_transfer_authority(
        plan(),
        transaction_id="tx-1",
        scope=TransferAuthorityScope.MATERIALIZE,
        authorization=policy(),
        authenticated_principal=principal(),
    )


def transaction():
    return TransferJournalEntry(
        "tx-1", TransferJournalPhase.PREPARED, WorkspaceTransfer.MIGRATE,
        "snapshot-1", "source-1", "dest-1",
    )


def run(tmp_path, **overrides):
    values = dict(
        plan=plan(), transaction=transaction(), authority=authority(), policy=policy(),
        principal_verifier=Verifier(), trust_roots=TrustRoots(),
        node_admission=Nodes(), key_admission=Keys(), transport=Transport(),
        revocations=AuthorityRevocationRegistry(tmp_path / "revocations.jsonl"),
        principal_id="principal-1", issuer_id="issuer-1", node_id="node-1", key_id="key-1",
        key_fingerprint=FINGERPRINT, claims={"role": "executor"}, signature=b"signature",
    )
    values.update(overrides)
    return executor_preflight(**values)


def test_unified_preflight_passes_all_gates(tmp_path):
    result = run(tmp_path)
    assert result.transaction_id == "tx-1"
    assert result.principal.principal_id == "principal-1"
    assert result.authority.authority_id
    assert result.transport.principal is result.principal


def test_forged_policy_digest_blocks(tmp_path):
    forged = replace(authority(), policy_digest="c" * 64)
    with pytest.raises(PermissionError, match="policy provenance"):
        run(tmp_path, authority=forged)


def test_forged_authority_id_blocks(tmp_path):
    forged = replace(authority(), authority_id="authority-forged")
    with pytest.raises(PermissionError, match="identity provenance"):
        run(tmp_path, authority=forged)


def test_policy_principal_mismatch_blocks(tmp_path):
    mismatched = PolicyAuthorization(
        AuthorityPrincipal("other-principal", "issuer-1"),
        AuthorityConstraints("dest-1", "snapshot-1"),
        True,
    )
    with pytest.raises(PermissionError, match="principal does not match policy"):
        run(tmp_path, policy=mismatched)


def test_unknown_trust_root_blocks_before_verifier(tmp_path):
    verifier = Verifier()
    with pytest.raises(PermissionError, match="issuer is not trusted"):
        run(tmp_path, trust_roots=type("Roots", (), {"issuer_fingerprint": lambda self, issuer: None})(), principal_verifier=verifier)
    assert verifier.calls == 0


def test_transport_peer_mismatch_closes_before_authority_use(tmp_path):
    transport = Transport(peer="evil-node")
    with pytest.raises(Exception, match="does not match principal"):
        run(tmp_path, transport=transport)
    assert transport.closed


def test_revoked_authority_blocks(tmp_path):
    revocations = AuthorityRevocationRegistry(tmp_path / "revocations.jsonl")
    revocations.revoke(authority().authority_id, reason="test")
    with pytest.raises(PermissionError, match="revoked"):
        run(tmp_path, revocations=revocations)


def test_journal_mismatch_blocks(tmp_path):
    bad_transaction = transaction().__class__(
        "tx-other", TransferJournalPhase.PREPARED, WorkspaceTransfer.MIGRATE,
        "snapshot-1", "source-1", "dest-1",
    )
    with pytest.raises(PermissionError, match="transaction"):
        run(tmp_path, transaction=bad_transaction)


def test_non_prepared_transaction_blocks(tmp_path):
    bad_transaction = transaction().__class__(
        "tx-1", TransferJournalPhase.MATERIALIZING, WorkspaceTransfer.MIGRATE,
        "snapshot-1", "source-1", "dest-1",
    )
    with pytest.raises(PermissionError, match="prepared"):
        run(tmp_path, transaction=bad_transaction)
