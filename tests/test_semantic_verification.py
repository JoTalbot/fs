from fs_overlay.semantic_verification import SemanticVerificationAdapter
from fs_overlay.verification import VerificationCheck, VerificationEvidence


def test_semantic_verification_requires_missing_evidence():
    adapter = SemanticVerificationAdapter()
    result = adapter.verify_required(
        (VerificationCheck("mount-isolated", "mount namespace is isolated"),),
        lambda check: None,
    )
    assert result.verified is False
    assert result.reasons == ("missing_evidence:mount-isolated",)


def test_semantic_verification_accepts_explicit_passing_evidence():
    adapter = SemanticVerificationAdapter()
    result = adapter.verify_required(
        (VerificationCheck("mount-isolated", "mount namespace is isolated"),),
        lambda check: VerificationEvidence(check.check_id, True, {"isolated": True}),
    )
    assert result.verified is True
    assert result.evidence[0].observed["isolated"] is True


def test_semantic_verification_propagates_failed_evidence_reason():
    adapter = SemanticVerificationAdapter()
    result = adapter.verify_required(
        (VerificationCheck("network", "network policy"),),
        lambda check: VerificationEvidence(check.check_id, False, {}, "network_not_isolated"),
    )
    assert result.verified is False
    assert result.reasons == ("network_not_isolated",)
