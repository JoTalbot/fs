from fs_overlay.federation_audit import FederationAuditTrail
from fs_overlay.federation_control import ReconciliationDecision
from fs_overlay.replication import ReplicaAction, ReplicaResult


def test_audit_records_decision_and_result(tmp_path) -> None:
    audit = FederationAuditTrail(tmp_path / "audit.journal")
    decision = ReconciliationDecision("obj", "a", "b", "REPLICATE", "restore desired replica count")
    records = audit.record_decisions([decision])
    assert records[0]["payload"]["event"] == "federation.reconciliation_decision"
    result = ReplicaResult(ReplicaAction("obj", "a", "b", "hash"), "SUCCEEDED", "hash", "replica verified")
    result_record = audit.record_result(result, causal_parent=records[0]["payload"]["event_hash"])
    assert result_record["payload"]["causal_parent"] == records[0]["payload"]["event_hash"]
    assert len(tuple(audit.log.replay())) == 2
