from fs_overlay.workspace_boundary import WorkspaceBoundaryProbeResult, probe_workspace_boundary


def test_workspace_boundary_result_is_explicit():
    result = WorkspaceBoundaryProbeResult(False, 1, "blocked")
    assert not result.supported
    assert result.returncode == 1
    assert result.detail == "blocked"


def test_workspace_boundary_probe_is_observational():
    result = probe_workspace_boundary(timeout=1.0)
    assert isinstance(result, WorkspaceBoundaryProbeResult)
    if result.supported:
        assert result.returncode == 0
        assert result.detail == "workspace_visible_host_root_absent"
