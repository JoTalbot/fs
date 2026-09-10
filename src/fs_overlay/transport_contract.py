"""Transport contract kept separate from federation semantics."""
from __future__ import annotations

from typing import Protocol


class FederationTransport(Protocol):
    def send(self, peer_node: str, payload: bytes) -> None: ...
    def receive(self) -> bytes | None: ...
    def close(self) -> None: ...
