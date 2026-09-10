from fs_overlay.linux_probe import NamespaceProbeResult, probe_namespace


def test_probe_rejects_unknown_namespace():
    try:
        probe_namespace("user")
    except ValueError as exc:
        assert "unsupported namespace" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_probe_result_is_explicit():
    result = NamespaceProbeResult("mount", False, 1, "blocked")
    assert not result.supported
    assert result.returncode == 1
    assert result.detail == "blocked"
