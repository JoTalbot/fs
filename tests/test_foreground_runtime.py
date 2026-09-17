from __future__ import annotations

import pytest

from fs_overlay.foreground_runtime import ForegroundRuntime


class FakeServer:
    def __init__(self):
        self.calls = []

    def start(self):
        self.calls.append("start")
        return "started"

    def stop(self):
        self.calls.append("stop")


def test_foreground_runtime_start_stop_and_context():
    server = FakeServer()
    with ForegroundRuntime(server) as runtime:
        assert runtime.started is True
        assert server.calls == ["start"]
    assert runtime.started is False
    assert server.calls == ["start", "stop"]


def test_foreground_runtime_rejects_double_start_and_wait_without_start():
    server = FakeServer()
    runtime = ForegroundRuntime(server)
    with pytest.raises(RuntimeError, match="not started"):
        runtime.wait()
    runtime.start()
    with pytest.raises(RuntimeError, match="already started"):
        runtime.start()
    runtime.stop()
    runtime.stop()
    assert server.calls == ["start", "stop"]


def test_foreground_runtime_stop_is_fail_safe():
    class BrokenServer(FakeServer):
        def stop(self):
            self.calls.append("stop")
            raise RuntimeError("stop failed")

    server = BrokenServer()
    runtime = ForegroundRuntime(server)
    runtime.start()
    with pytest.raises(RuntimeError, match="stop failed"):
        runtime.stop()
    assert runtime.started is False
    assert server.calls == ["start", "stop"]
