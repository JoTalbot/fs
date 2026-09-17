import platform

from fs_overlay.workspace_boundary import WorkspaceBoundaryProbeResult, probe_workspace_boundary


def test_workspace_boundary_result_is_explicit():
    result = WorkspaceBoundaryProbeResult(False, 1, "blocked")
    assert not result.supported
    assert result.returncode == 1
    assert result.detail == "blocked"


def test_workspace_boundary_probe_is_observational(monkeypatch):
    monkeypatch.setattr("fs_overlay.workspace_boundary.platform.system", lambda: "Linux")
    result = probe_workspace_boundary(timeout=1.0)
    assert isinstance(result, WorkspaceBoundaryProbeResult)
    if result.supported:
        assert result.returncode == 0
        assert result.detail == "workspace_visible_host_root_absent"


def test_workspace_boundary_fails_closed_off_linux(monkeypatch):
    monkeypatch.setattr("fs_overlay.workspace_boundary.platform.system", lambda: "FreeBSD")
    result = probe_workspace_boundary()
    assert result == WorkspaceBoundaryProbeResult(False, None, "host_is_not_linux")


def test_workspace_boundary_reports_missing_backend(monkeypatch):
    monkeypatch.setattr("fs_overlay.workspace_boundary.platform.system", lambda: "Linux")
    monkeypatch.setattr("fs_overlay.workspace_boundary.shutil.which", lambda _: None)
    result = probe_workspace_boundary()
    assert result == WorkspaceBoundaryProbeResult(False, None, "bubblewrap_unavailable")
