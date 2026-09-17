"""Bounded foreground lifecycle for local FS services."""
from __future__ import annotations

import threading
from typing import Protocol


class StoppableServer(Protocol):
    """Minimal lifecycle contract required by the foreground runtime."""

    def start(self): ...

    def stop(self) -> None: ...


class ForegroundRuntime:
    """Run a local server in the foreground until explicitly stopped."""

    def __init__(self, server: StoppableServer) -> None:
        self.server = server
        self._stop = threading.Event()
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    def start(self):
        if self._started:
            raise RuntimeError("foreground runtime is already started")
        result = self.server.start()
        self._stop.clear()
        self._started = True
        return result

    def stop(self) -> None:
        if not self._started:
            return
        self._stop.set()
        try:
            self.server.stop()
        finally:
            self._started = False

    def wait(self) -> None:
        if not self._started:
            raise RuntimeError("foreground runtime is not started")
        try:
            self._stop.wait()
        except KeyboardInterrupt:
            self.stop()
            raise

    def run(self):
        result = self.start()
        try:
            self.wait()
        except KeyboardInterrupt:
            return result
        finally:
            self.stop()
        return result

    def __enter__(self) -> "ForegroundRuntime":
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.stop()
