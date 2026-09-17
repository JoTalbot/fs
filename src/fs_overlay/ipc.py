"""Local Unix-domain IPC transport for the FS control plane.

Unix-domain sockets provide process-local IPC without exposing a TCP listener.
The protocol remains the same framed semantic message format used by the
loopback server; IPC does not grant authority by itself.
"""
from __future__ import annotations

import os
import socket
import threading
from pathlib import Path
from typing import Any

from .genesis_service import GenesisService
from .transport import recv_message, send_message


class UnixSocketServer:
    """Genesis service server bound to a filesystem Unix-domain socket."""

    def __init__(self, service: GenesisService, path: str | os.PathLike[str], *, backlog: int = 8) -> None:
        if not hasattr(socket, "AF_UNIX"):
            raise RuntimeError("Unix-domain sockets are unavailable on this platform")
        socket_path = Path(path)
        if not socket_path.is_absolute():
            raise ValueError("Unix socket path must be absolute")
        if len(str(socket_path).encode()) >= 108:
            raise ValueError("Unix socket path is too long")
        self.service = service
        self.path = socket_path
        self.backlog = backlog
        self._socket: socket.socket | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> str | None:
        return str(self.path) if self._socket is not None else None

    def start(self) -> str:
        if self._socket is not None:
            raise RuntimeError("server is already started")
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(str(self.path))
            os.chmod(self.path, 0o600)
            listener.listen(self.backlog)
            listener.settimeout(0.25)
        except Exception:
            listener.close()
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            raise
        self._socket = listener
        self._stop.clear()
        self._thread = threading.Thread(target=self._serve, name="fs-genesis-ipc", daemon=True)
        self._thread.start()
        return str(self.path)

    def stop(self) -> None:
        self._stop.set()
        listener, self._socket = self._socket, None
        if listener is not None:
            listener.close()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

    def _serve(self) -> None:
        listener = self._socket
        if listener is None:
            return
        while not self._stop.is_set():
            try:
                connection, _ = listener.accept()
            except (TimeoutError, socket.timeout):
                continue
            except OSError:
                if self._stop.is_set():
                    return
                continue
            with connection:
                connection.settimeout(5.0)
                try:
                    response = self.service.handle(recv_message(connection))
                    send_message(connection, {
                        "ok": response.ok,
                        "operation": response.operation,
                        "data": dict(response.data),
                        "error": response.error,
                    })
                except (ConnectionError, ValueError, TypeError):
                    continue
                except Exception:
                    continue

    def __enter__(self) -> "UnixSocketServer":
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.stop()


class UnixSocketTransport:
    """Client for a local Unix-domain FS control-plane endpoint."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        if not hasattr(socket, "AF_UNIX"):
            raise RuntimeError("Unix-domain sockets are unavailable on this platform")
        socket_path = Path(path)
        if not socket_path.is_absolute():
            raise ValueError("Unix socket path must be absolute")
        self.path = socket_path

    def request(self, message: dict[str, Any], timeout: float = 5.0) -> dict[str, Any]:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect(str(self.path))
            send_message(sock, message)
            return recv_message(sock)
