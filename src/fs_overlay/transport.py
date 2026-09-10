"""Minimal localhost transport for FS control-plane messages.

The transport is intentionally loopback-only and message-framed. It carries
semantic requests; it does not grant authority or bypass host security.
"""
from __future__ import annotations

import json
import socket
import struct
from typing import Any

_MAX_MESSAGE = 1024 * 1024


def _pack(message: dict[str, Any]) -> bytes:
    payload = json.dumps(message, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(payload) > _MAX_MESSAGE:
        raise ValueError("message exceeds transport limit")
    return struct.pack("!I", len(payload)) + payload


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("transport closed before message was complete")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_message(sock: socket.socket, message: dict[str, Any]) -> None:
    sock.sendall(_pack(message))


def recv_message(sock: socket.socket) -> dict[str, Any]:
    header = _recv_exact(sock, 4)
    (size,) = struct.unpack("!I", header)
    if size > _MAX_MESSAGE:
        raise ValueError("incoming message exceeds transport limit")
    value = json.loads(_recv_exact(sock, size).decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("transport message must be a JSON object")
    return value


class LocalhostTransport:
    """Loopback TCP transport with no external-network binding."""

    def __init__(self, host: str = "127.0.0.1") -> None:
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise ValueError("LocalhostTransport accepts loopback addresses only")
        self.host = host

    def request(self, port: int, message: dict[str, Any], timeout: float = 5.0) -> dict[str, Any]:
        with socket.create_connection((self.host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            send_message(sock, message)
            return recv_message(sock)
