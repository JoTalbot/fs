"""Fail-closed transport session gate.

The gate deliberately does not implement cryptography. An injected
``AuthenticatedTransport`` is responsible for authenticated encryption and
peer authentication; this layer binds that authenticated session to the
already-verified principal and rejects peer changes or replayed frames.
"""
from __future__ import annotations

import struct

from .identity_verification import AuthenticatedPrincipal
from .production_adapters import AuthenticatedTransport

_HEADER = struct.Struct("!Q")


class TransportSecurityError(PermissionError):
    """Raised when an authenticated transport session violates its contract."""


class FailClosedTransportGate:
    """Bind an authenticated transport to one principal and monotonic frames."""

    def __init__(self, transport: AuthenticatedTransport, principal: AuthenticatedPrincipal) -> None:
        self._transport = transport
        self._principal = principal
        self._send_sequence = 0
        self._receive_sequence = 0
        self._closed = False

    @property
    def principal(self) -> AuthenticatedPrincipal:
        return self._principal

    def _fail(self, message: str) -> None:
        self._closed = True
        try:
            self._transport.close()
        finally:
            raise TransportSecurityError(message)

    def _close_after_provider_failure(self) -> None:
        """Invalidate and close the provider session after any transport error."""
        self._closed = True
        try:
            self._transport.close()
        except Exception:
            pass

    def _require_session(self) -> None:
        if self._closed:
            raise TransportSecurityError("transport session is closed")
        try:
            authenticated = self._transport.is_authenticated()
            peer = self._transport.peer_node()
        except Exception:
            self._close_after_provider_failure()
            raise TransportSecurityError("authenticated transport session state could not be validated")
        if not authenticated:
            self._fail("authenticated transport session is not authenticated")
        if peer != self._principal.node_id:
            self._fail("authenticated transport peer does not match principal node")

    def validate_session(self) -> None:
        """Validate the bound session immediately, without sending data."""
        self._require_session()

    def send(self, payload: bytes) -> None:
        self._require_session()
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        sequence = self._send_sequence + 1
        frame = _HEADER.pack(sequence) + payload
        try:
            self._transport.send(self._principal.node_id, frame)
        except Exception:
            self._close_after_provider_failure()
            raise
        self._send_sequence = sequence

    def receive(self) -> bytes | None:
        self._require_session()
        try:
            frame = self._transport.receive()
        except Exception:
            self._close_after_provider_failure()
            raise
        if frame is None:
            return None
        if not isinstance(frame, bytes) or len(frame) < _HEADER.size:
            self._fail("malformed authenticated transport frame")
        sequence = _HEADER.unpack(frame[:_HEADER.size])[0]
        expected = self._receive_sequence + 1
        if sequence != expected:
            self._fail("authenticated transport replay or sequence violation")
        self._receive_sequence = sequence
        return frame[_HEADER.size:]

    def close(self) -> None:
        self._closed = True
        self._transport.close()
