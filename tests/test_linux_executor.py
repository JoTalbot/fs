from fs_overlay.linux_executor import LinuxExecutionPolicy, LinuxNamespaceExecutor


class FakeBackend:
    def wrap(self, argv):
        return ("/usr/bin/unshare", "--mount", *argv)


class FakeWorkspaceBackend:
    def wrap(self, argv, *, workspace_path):
        return ("/usr/bin/bwrap", "--ro-bind", workspace_path, "/workspace", "--", *argv)


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
    assert calls["argv"] == ["/usr/bin/unshare", "--mount", "/bin/echo", "ok"]
    assert calls["kwargs"]["shell"] is False


def test_executor_passes_explicit_workspace_to_workspace_backend(monkeypatch, tmp_path):
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
    assert calls["argv"] == ["/usr/bin/bwrap", "--ro-bind", str(tmp_path), "/workspace", "--", "/bin/echo", "ok"]
    assert calls["kwargs"]["cwd"] is None
    assert calls["kwargs"]["shell"] is False
