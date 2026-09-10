from fs_overlay.linux_executor import LinuxExecutionPolicy, LinuxNamespaceExecutor


class FakeBackend:
    name = "fake-linux-backend"

    def wrap(self, argv):
        return ("/usr/bin/unshare", "--mount", *argv)


class FakeWorkspaceBackend:
    name = "bubblewrap-workspace"
    boundary_check_exit_codes = (125, 126)

    def wrap(self, argv, *, workspace_path, network, read_only):
        return (
            "/usr/bin/bwrap",
            "--network=" + network,
            "--ro-bind" if read_only else "--bind",
            workspace_path,
            "/workspace",
            "--",
            *argv,
        )


def test_executor_requires_admission():
    result = LinuxNamespaceExecutor(FakeBackend()).execute(("/bin/true",))
    assert result.status == "rejected"


def test_executor_rejects_unenforced_policy():
    result = LinuxNamespaceExecutor(FakeBackend()).execute(
        ("/bin/true",), admitted=True,
        policy=LinuxExecutionPolicy(filesystem="workspace-only"),
    )
    assert result.status == "rejected"
    assert "workspace_path_required" in result.stderr


def test_executor_uses_backend_without_shell(monkeypatch):
    calls = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(argv, **kwargs):
        calls["argv"] = argv
        calls["kwargs"] = kwargs
        return Completed()

    monkeypatch.setattr("fs_overlay.linux_executor.subprocess.run", fake_run)
    result = LinuxNamespaceExecutor(FakeBackend()).execute(
        ("/bin/echo", "ok"), admitted=True,
    )
    assert result.status == "succeeded"
    assert result.backend == "fake-linux-backend"
    assert result.execution_evidence == ()
    assert calls["argv"] == ["/usr/bin/unshare", "--mount", "/bin/echo", "ok"]
    assert calls["kwargs"]["shell"] is False


def test_executor_passes_explicit_workspace_and_network_to_workspace_backend(monkeypatch, tmp_path):
    calls = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(argv, **kwargs):
        calls["argv"] = argv
        calls["kwargs"] = kwargs
        return Completed()

    monkeypatch.setattr("fs_overlay.linux_executor.subprocess.run", fake_run)
    result = LinuxNamespaceExecutor(FakeBackend(), FakeWorkspaceBackend()).execute(
        ("/bin/echo", "ok"),
        admitted=True,
        policy=LinuxExecutionPolicy(filesystem="workspace-only", network="deny"),
        workspace_path=str(tmp_path),
    )
    assert result.status == "succeeded"
    assert result.backend == "bubblewrap-workspace"
    assert result.execution_evidence == (
        "workspace-filesystem-boundary-observed",
        "network-namespace-observed",
    )
    assert calls["argv"] == [
        "/usr/bin/bwrap", "--network=deny", "--ro-bind", str(tmp_path),
        "/workspace", "--", "/bin/echo", "ok",
    ]
    assert calls["kwargs"]["cwd"] is None
    assert calls["kwargs"]["shell"] is False


def test_executor_passes_writable_workspace_mode(monkeypatch, tmp_path):
    calls = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(argv, **kwargs):
        calls["argv"] = argv
        return Completed()

    monkeypatch.setattr("fs_overlay.linux_executor.subprocess.run", fake_run)
    result = LinuxNamespaceExecutor(FakeBackend(), FakeWorkspaceBackend()).execute(
        ("/bin/true",),
        admitted=True,
        policy=LinuxExecutionPolicy(filesystem="workspace-only", network="host"),
        workspace_path=str(tmp_path),
        workspace_read_only=False,
    )
    assert result.status == "succeeded"
    assert "--bind" in calls["argv"]
    assert "--ro-bind" not in calls["argv"]
    assert result.execution_evidence == ("workspace-filesystem-boundary-observed",)


def test_executor_preserves_host_network_policy_for_workspace_backend(monkeypatch, tmp_path):
    calls = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(argv, **kwargs):
        calls["argv"] = argv
        return Completed()

    monkeypatch.setattr("fs_overlay.linux_executor.subprocess.run", fake_run)
    result = LinuxNamespaceExecutor(FakeBackend(), FakeWorkspaceBackend()).execute(
        ("/bin/true",),
        admitted=True,
        policy=LinuxExecutionPolicy(filesystem="workspace-only", network="host"),
        workspace_path=str(tmp_path),
    )
    assert result.status == "succeeded"
    assert result.execution_evidence == ("workspace-filesystem-boundary-observed",)
    assert "--network=host" in calls["argv"]


def test_executor_fails_closed_on_reserved_boundary_failure(monkeypatch, tmp_path):
    class Completed:
        returncode = 125
        stdout = ""
        stderr = "boundary failed"

    monkeypatch.setattr("fs_overlay.linux_executor.subprocess.run", lambda *a, **k: Completed())
    result = LinuxNamespaceExecutor(FakeBackend(), FakeWorkspaceBackend()).execute(
        ("/bin/true",),
        admitted=True,
        policy=LinuxExecutionPolicy(filesystem="workspace-only", network="deny"),
        workspace_path=str(tmp_path),
    )
    assert result.status == "failed"
    assert result.execution_evidence == ()
