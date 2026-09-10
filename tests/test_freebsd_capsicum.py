from fs_overlay.freebsd_capsicum import FreeBSDCapsicumBackend


def test_capsicum_is_fail_closed_off_platform(monkeypatch):
    monkeypatch.setattr("fs_overlay.freebsd_capsicum.platform.system", lambda: "Linux")
    result = FreeBSDCapsicumBackend().plan()
    assert not result.available
    assert not result.verified
    assert result.reason == "host is not FreeBSD"


def test_capsicum_does_not_claim_execution_evidence_during_planning(monkeypatch):
    monkeypatch.setattr("fs_overlay.freebsd_capsicum.platform.system", lambda: "FreeBSD")
    result = FreeBSDCapsicumBackend().plan()
    assert result.available
    assert not result.verified
    assert result.reason == "cap_enter requires execution in the workload process"


def test_capsicum_native_entrypoint_is_not_used_off_platform(monkeypatch):
    monkeypatch.setattr("fs_overlay.freebsd_capsicum.platform.system", lambda: "Linux")
    result = FreeBSDCapsicumBackend().enter_current_process()
    assert not result.available
    assert not result.verified
    assert result.reason == "host is not FreeBSD"
