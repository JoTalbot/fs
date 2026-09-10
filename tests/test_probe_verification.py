from fs_overlay.evidence_provider import default_evidence_provider
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


def test_workspace_provider_rejects_generic_or_wrong_backend_evidence():
    check = VerificationCheck("workspace:boundary", "workspace boundary")
    evidence = default_evidence_provider(
        check,
        execution_result=type(
            "Result", (), {"backend": "native-process", "execution_evidence": ("workspace:boundary-observed",)}
        )(),
    )
    assert evidence is not None
    assert not evidence.passed


def test_workspace_provider_accepts_exact_execution_evidence():
    check = VerificationCheck("workspace:boundary", "workspace boundary")
    result = type(
        "Result", (), {
            "backend": "bubblewrap-workspace",
            "execution_evidence": ("workspace:boundary-observed",),
        }
    )()
    evidence = default_evidence_provider(check, execution_result=result)
    assert evidence is not None
    assert evidence.passed
    assert evidence.observed["backend"] == "bubblewrap-workspace"
