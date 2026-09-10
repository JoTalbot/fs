from fs_overlay.linux_executor import LinuxExecutionPolicy, LinuxNamespaceExecutor


class FakeBackend:
    def wrap(self, argv):
        return ("/usr/bin/unshare", "--mount", *argv)


def test_executor_requires_admission():
    result = LinuxNamespaceExecutor(FakeBackend()).execute(("/bin/true",))
    assert result.status == "rejected"


def test_executor_rejects_unenforced_policy():
    result = LinuxNamespaceExecutor(FakeBackend()).execute(
        ("/bin/true",), admitted=True,
        policy=LinuxExecutionPolicy(filesystem="workspace-only"),
    )
    assert result.status == "rejected"
    assert "not enforced" in result.stderr


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
