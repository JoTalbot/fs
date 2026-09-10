"""Plan explicit Linux network namespace isolation.

This module is plan-only. Merely finding ``unshare`` is not treated as proof
that the kernel permits an unprivileged network namespace, so execution must
still verify the resulting isolation before committing state.
"""
from __future__ import annotations

from dataclasses import dataclass
import platform
import shutil


@dataclass(frozen=True, slots=True)
class NetworkNamespacePlan:
    available: bool
    admitted: bool
    backend: str = "linux-network-namespace"
    argv_prefix: tuple[str, ...] = ()
    guarantees: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


def plan_network_namespace(*, requested: str = "deny") -> NetworkNamespacePlan:
    reasons: list[str] = []
    if requested not in {"host", "deny"}:
        reasons.append("unsupported_network_policy")
    if requested == "host":
        return NetworkNamespacePlan(True, True, guarantees=("host-network",))
    if platform.system().lower() != "linux":
        reasons.append("host_is_not_linux")
    unshare = shutil.which("unshare")
    if unshare is None:
        reasons.append("unshare_utility_unavailable")
    if reasons:
        return NetworkNamespacePlan(False, False, reasons=tuple(reasons))
    return NetworkNamespacePlan(
        True,
        True,
        argv_prefix=(unshare, "--net"),
        guarantees=("network-namespace", "network-deny-requested"),
        reasons=("kernel_policy_may_reject_unprivileged_network_namespace",),
    )
