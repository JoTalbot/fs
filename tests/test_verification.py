from fs_overlay.verification import (
    VerificationCheck,
    VerificationEvidence,
    verify,
)


def test_required_check_needs_evidence():
    result = verify((VerificationCheck("mount", "mount namespace"),), lambda _: None)
    assert not result.verified
    assert result.reasons == ("missing_evidence:mount",)


def test_failed_required_evidence_fails_closed():
    check = VerificationCheck("network", "network namespace")

    def provider(_):
        return VerificationEvidence("network", False, {"isolated": False}, "network_not_isolated")

    result = verify((check,), provider)
    assert not result.verified
    assert result.reasons == ("network_not_isolated",)


def test_optional_missing_evidence_does_not_fail():
    result = verify((VerificationCheck("hint", "optional hint", False),), lambda _: None)
    assert result.verified
