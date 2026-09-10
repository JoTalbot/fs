"""Minimal local Genesis service for the FS reference runtime.

The service is deliberately transport-agnostic. It exposes a tiny request
surface around node identity, admission, capability inspection and execution.
It never grants authority and never mutates the host during bootstrap.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .identity import NodeIdentity


@dataclass(frozen=True, slots=True)
class ServiceResponse:
    ok: bool
    operation: str
    data: Mapping[str, Any]
    error: str | None = None


class GenesisService:
    """Reference service implementing the smallest useful FS node boundary."""

    def __init__(
        self,
        identity: NodeIdentity,
        capabilities: Mapping[str, Any],
        *,
        admitted: bool = False,
        executor: Callable[[tuple[str, ...]], Mapping[str, Any]] | None = None,
    ) -> None:
        self.identity = identity
        self.capabilities = dict(capabilities)
        self.admitted = admitted
        self._executor = executor

    def handle(self, request: Mapping[str, Any]) -> ServiceResponse:
        operation = str(request.get("operation", ""))
        if not operation:
            return ServiceResponse(False, "", {}, "missing operation")

        if operation == "ping":
            return ServiceResponse(True, operation, {"ready": self.admitted})
        if operation == "identity":
            return ServiceResponse(
                True,
                operation,
                {
                    "node_id": self.identity.node_id,
                    "public_key_fingerprint": self.identity.public_key_fingerprint,
                    "protocol_version": self.identity.protocol_version,
                },
            )
        if operation == "capabilities":
            return ServiceResponse(True, operation, dict(self.capabilities))
        if operation == "admit":
            if request.get("node_id") != self.identity.node_id:
                return ServiceResponse(False, operation, {}, "node identity mismatch")
            self.admitted = True
            return ServiceResponse(True, operation, {"admitted": True})
        if operation == "execute":
            if not self.admitted:
                return ServiceResponse(False, operation, {}, "node is not admitted")
            argv = request.get("argv")
            if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
                return ServiceResponse(False, operation, {}, "argv must be a non-empty string list")
            if self._executor is None:
                return ServiceResponse(False, operation, {}, "no execution backend configured")
            return ServiceResponse(True, operation, dict(self._executor(tuple(argv))))

        return ServiceResponse(False, operation, {}, f"unsupported operation: {operation}")
