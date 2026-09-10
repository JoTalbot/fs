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


def test_probe_namespace_requires_observed_identity_change(monkeypatch):
    class Completed:
        returncode = 0
        stdout = "mnt:[4026531840]\n"
        stderr = ""

    monkeypatch.setattr("fs_overlay.linux_probe.platform.system", lambda: "Linux")
    monkeypatch.setattr("fs_overlay.linux_probe.shutil.which", lambda _: "/usr/bin/unshare")
    monkeypatch.setattr("fs_overlay.linux_probe.os.readlink", lambda _: "mnt:[4026531840]")
    monkeypatch.setattr("fs_overlay.linux_probe.subprocess.run", lambda *args, **kwargs: Completed())

    result = probe_namespace("mount")

    assert not result.supported
    assert result.detail == "namespace_identity_unchanged"


def test_probe_namespace_accepts_observed_identity_change(monkeypatch):
    class Completed:
        returncode = 0
        stdout = "mnt:[4026532325]\n"
        stderr = ""

    monkeypatch.setattr("fs_overlay.linux_probe.platform.system", lambda: "Linux")
    monkeypatch.setattr("fs_overlay.linux_probe.shutil.which", lambda _: "/usr/bin/unshare")
    monkeypatch.setattr("fs_overlay.linux_probe.os.readlink", lambda _: "mnt:[4026531840]")
    monkeypatch.setattr("fs_overlay.linux_probe.subprocess.run", lambda *args, **kwargs: Completed())

    result = probe_namespace("mount")

    assert result.supported
    assert result.detail == "namespace_identity_changed"
