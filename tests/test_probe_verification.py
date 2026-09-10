from fs_overlay.probe_verification import linux_namespace_evidence
from fs_overlay.verification import VerificationCheck


def test_non_namespace_check_has_no_provider_evidence():
    assert linux_namespace_evidence(VerificationCheck("mount:workspace", "workspace")) is None


def test_namespace_provider_returns_explicit_evidence(monkeypatch):
    class Result:
        namespace = "mount"
        supported = True
        returncode = 0
        detail = "probe_succeeded"

    monkeypatch.setattr("fs_overlay.probe_verification.probe_namespace", lambda name: Result())
    evidence = linux_namespace_evidence(VerificationCheck("namespace:mount", "mount namespace"))
    assert evidence is not None
    assert evidence.check_id == "namespace:mount"
    assert evidence.passed
    assert evidence.observed["namespace"] == "mount"
