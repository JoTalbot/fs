"""Safe assembly of the Genesis service and native process adapter."""
from __future__ import annotations

from typing import Any

from .adapter import NativeProcessAdapter
from .capabilities import discover_local_capabilities
from .genesis_service import GenesisService
from .identity import NodeIdentity


def build_local_service(
    identity: NodeIdentity,
    capabilities: dict[str, Any] | None = None,
) -> GenesisService:
    """Create a local service without starting listeners or changing the host.

    When no explicit snapshot is supplied, capabilities are observed locally.
    Observation remains informational and does not imply resource sharing or
    federation admission.
    """
    adapter = NativeProcessAdapter()
    observed = capabilities if capabilities is not None else discover_local_capabilities().to_dict()

    def execute(argv: tuple[str, ...]) -> dict[str, Any]:
        result = adapter.execute(argv, admitted=True, timeout=30.0)
        return {
            "status": result.status,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": result.timed_out,
        }

    return GenesisService(identity, observed, executor=execute)
