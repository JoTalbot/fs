from __future__ import annotations

import pytest

from fs_overlay.authority_policy import AuthorityConstraints, AuthorityPrincipal, PolicyAuthorization
from fs_overlay.authority_revocation import AuthorityRevocationRegistry
from fs_overlay.executor_preflight import executor_preflight
from fs_overlay.identity_verification import AuthenticatedPrincipal
from fs_overlay.transport_gate import TransportSecurityError
from fs_overlay.workspace_migration import WorkspaceTransfer, WorkspaceTransferPlan
from fs_overlay.workspace_transfer_authority import TransferAuthority, TransferAuthorityScope
from fs_overlay.workspace_transfer_journal import TransferJournalEntry, TransferJournalPhase


_DIGEST = "a" * 64


class Verifier:
    def __init__(self):
        self.calls = 0

    def verify(self, **kwargs):
        self.calls += 1
        return AuthenticatedPrincipal(
            principal_id=kwargs["principal_id"],
            issuer_id=kwargs["issuer_id"],
            node_id=kwargs["node_id"],
            key_id=kwargs["key_id"],
            key_fingerprint=kwargs["key_fingerprint"],
            trust_root_id="root-1",
            claims_digest=_DIGEST,
        )


class Roots:
    def issuer_fingerprint(self, issuer):
        return _DIGEST


class Nodes:
    def is_admitted(self, node_id, fingerprint):
        return True


class Keys:
    def is_admitted(self, node_id, key_id, fingerprint):
        return True

    def can_verify(self, node_id, key_id):
        return True


class Transport:
    def __init__(self, peer="node-1"):
        self.peer = peer
        self.closed = False
        self.authenticated = True

    def authenticate(self, peer_node):
        return None

    def send(self, peer_node, payload):
        return None

    def receive(self):
        return b""

    def peer_node(self):
        return self.peer

    def is_authenticated(self):
        return self.authenticated

    def close(self):
        self.closed = True


def run(tmp_path, **overrides):
    plan = WorkspaceTransferPlan(
        operation=WorkspaceTransfer.MIGRATE,
        source_workspace_id="source-1",
        destination_workspace_id="dest-1",
        snapshot_id="snap-1",
        destination_path="/future/materialize",
        ready=True,
        source_preserved=True,
    )
    transaction = TransferJournalEntry(
        transaction_id="tx-1",
        operation=WorkspaceTransfer.MIGRATE,
        snapshot_id="snap-1",
        source_workspace_id="source-1",
        destination_workspace_id="dest-1",
        phase=TransferJournalPhase.PREPARED,
    )
    principal = AuthenticatedPrincipal(
        principal_id="principal-1",
        issuer_id="issuer-1",
        node_id="node-1",
        key_id="key-1",
        key_fingerprint=_DIGEST,
        trust_root_id="root-1",
        claims_digest=_DIGEST,
    )
    authorization = PolicyAuthorization(
        principal=AuthorityPrincipal(principal_id=principal.principal_id, issuer_id=principal.issuer_id),
        constraints=AuthorityConstraints(workspace_id="dest-1", snapshot_id="snap-1"),
        approved=True,
    )
    authority = TransferAuthority(
        transaction_id="tx-1",
        snapshot_id="snap-1",
        source_workspace_id="source-1",
        destination_workspace_id="dest-1",
        scope=TransferAuthorityScope.MATERIALIZE,
        principal_id=principal.principal_id,
        issuer_id=principal.issuer_id,
        policy_digest=_DIGEST,
        authority_id="authority-1",
    )
    values = dict(
        plan=plan,
        transaction=transaction,
        authority=authority,
        policy=authorization,
        principal_verifier=Verifier(),
        trust_roots=Roots(),
        node_admission=Nodes(),
        key_admission=Keys(),
        transport=Transport(),
        revocations=AuthorityRevocationRegistry(tmp_path / "revocations.jsonl"),
        principal_id=principal.principal_id,
        issuer_id=principal.issuer_id,
        node_id=principal.node_id,
        key_id=principal.key_id,
        key_fingerprint=principal.key_fingerprint,
        claims={"sub": principal.principal_id},
        signature=b"signature",
    )
    values.update(overrides)
    return executor_preflight(**values)


def test_unified_preflight_passes_all_gates(tmp_path):
    result = run(tmp_path)
    assert result.transaction_id == "tx-1"
    assert result.principal.principal_id == "principal-1"
    assert result.authority.authority_id == "authority-1"
    assert result.transport.principal is result.principal


def test_unknown_trust_root_blocks_before_verifier(tmp_path):
    verifier = Verifier()
    with pytest.raises(PermissionError, match="trusted issuer"):
        run(tmp_path, trust_roots=type("Roots", (), {"issuer_fingerprint": lambda self, issuer: None})(), principal_verifier=verifier)
    assert verifier.calls == 0


def test_transport_peer_mismatch_closes_before_authority_use(tmp_path):
    transport = Transport(peer="evil-node")
    with pytest.raises(Exception, match="does not match principal"):
        run(tmp_path, transport=transport)
    assert transport.closed


def test_revoked_authority_blocks(tmp_path):
    revocations = AuthorityRevocationRegistry(tmp_path / "revocations.jsonl")
    revocations.revoke("authority-1", reason="test")
    with pytest.raises(PermissionError, match="revoked"):
        run(tmp_path, revocations=revocations)


def test_journal_mismatch_blocks(tmp_path):
    transaction = TransferJournalEntry(
        transaction_id="tx-other",
        operation=WorkspaceTransfer.MIGRATE,
        snapshot_id="snap-1",
        source_workspace_id="source-1",
        destination_workspace_id="dest-1",
        phase=TransferJournalPhase.PREPARED,
    )
    with pytest.raises(PermissionError, match="transaction"):
        run(tmp_path, transaction=transaction)


def test_non_prepared_transaction_blocks(tmp_path):
    transaction = TransferJournalEntry(
        transaction_id="tx-1",
        operation=WorkspaceTransfer.MIGRATE,
        snapshot_id="snap-1",
        source_workspace_id="source-1",
        destination_workspace_id="dest-1",
        phase=TransferJournalPhase.PREPARING,
    )
    with pytest.raises(PermissionError, match="prepared"):
        run(tmp_path, transaction=transaction)
