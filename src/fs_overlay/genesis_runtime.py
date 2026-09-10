"""Safe assembly of the Genesis service and native process adapter."""
from __future__ import annotations

from typing import Any

from .adapter import NativeProcessAdapter
from .genesis_service import GenesisService
from .identity import NodeIdentity


def build_local_service(identity: NodeIdentity, capabilities: dict[str, Any]) -> GenesisService:
    """Create a local service without starting listeners or changing the host."""
    adapter = NativeProcessAdapter()

    def execute(argv: tuple[str, ...]) -> dict[str, Any]:
        result = adapter.execute(argv, admitted=True, timeout=30.0)
        return {
            "status": result.status,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": result.timed_out,
        }

    return GenesisService(identity, capabilities, executor=execute)
