"""Loopback-only request server for the local Genesis service."""
from __future__ import annotations

import socket
import threading
from typing import Any, Mapping

from .genesis_service import GenesisService, ServiceResponse
from .transport import recv_message, send_message


class GenesisServer:
    """Small, bounded localhost server around a GenesisService instance."""

    def __init__(
        self,
        service: GenesisService,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
        backlog: int = 8,
    ) -> None:
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise ValueError("GenesisServer accepts loopback addresses only")
        if not 0 <= port <= 65535:
            raise ValueError("port must be between 0 and 65535")
        self.service = service
        self.host = host
        self.port = port
        self.backlog = backlog
        self._socket: socket.socket | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> tuple[str, int] | None:
        if self._socket is None:
            return None
        bound = self._socket.getsockname()
        return str(bound[0]), int(bound[1])

    def start(self) -> tuple[str, int]:
        if self._socket is not None:
            raise RuntimeError("server is already started")
        family = socket.AF_INET6 if ":" in self.host else socket.AF_INET
        listener = socket.socket(family, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.listen(self.backlog)
        listener.settimeout(0.25)
        self._socket = listener
        self._stop.clear()
        self._thread = threading.Thread(target=self._serve, name="fs-genesis", daemon=True)
        self._thread.start()
        address = self.address
        assert address is not None
        return address

    def stop(self) -> None:
        self._stop.set()
        listener, self._socket = self._socket, None
        if listener is not None:
            listener.close()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

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
                    request = recv_message(connection)
                    response = self._handle(request)
                except (ConnectionError, ValueError, TypeError) as exc:
                    response = ServiceResponse(False, "", {}, str(exc))
                send_message(connection, self._encode(response))

    def _handle(self, request: Mapping[str, Any]) -> ServiceResponse:
        return self.service.handle(request)

    @staticmethod
    def _encode(response: ServiceResponse) -> dict[str, Any]:
        return {
            "ok": response.ok,
            "operation": response.operation,
            "data": dict(response.data),
            "error": response.error,
        }

    def __enter__(self) -> "GenesisServer":
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.stop()
