"""Capability-aware backend selection for FS environments."""

from __future__ import annotations

from dataclasses import dataclass

from .model import CapabilitySet, EnvironmentSpec


@dataclass(frozen=True, slots=True)
class BackendDecision:
    backend: str | None
    eligible: bool
    reasons: tuple[str, ...] = ()
    score: float = 0.0


class BackendPlanner:
    """Select the least powerful backend that satisfies the policy.

    The planner is intentionally conservative: unknown capabilities never count
    as support. This prevents adaptive behaviour from becoming accidental
    privilege escalation.
    """

    ORDER = ("native", "container", "microvm", "vm")

    def plan(self, spec: EnvironmentSpec, caps: CapabilitySet) -> tuple[BackendDecision, ...]:
        requested = spec.policy.runtime
        candidates = (requested,) if requested != "auto" else self.ORDER
        decisions: list[BackendDecision] = []
        for backend in candidates:
            decisions.append(self._evaluate(backend, spec, caps))
        return tuple(decisions)

    def select(self, spec: EnvironmentSpec, caps: CapabilitySet) -> BackendDecision:
        decisions = self.plan(spec, caps)
        eligible = [d for d in decisions if d.eligible]
        if not eligible:
            return BackendDecision(
                backend=None,
                eligible=False,
                reasons=tuple(r for d in decisions for r in d.reasons),
            )
        return max(eligible, key=lambda d: (d.score, -self.ORDER.index(d.backend)))

    def _evaluate(
        self, backend: str, spec: EnvironmentSpec, caps: CapabilitySet
    ) -> BackendDecision:
        reasons: list[str] = []

        if backend not in self.ORDER:
            return BackendDecision(backend, False, ("unsupported_backend",))

        isolation_required = spec.policy.filesystem not in {"host", "workspace-only"} or spec.policy.allow_privileged is False

        if backend == "native":
            if spec.policy.filesystem not in {"host", "workspace-only"}:
                reasons.append("filesystem_isolation_required")
            if spec.policy.network not in {"host", "deny"}:
                reasons.append("network_policy_requires_isolation")
            eligible = not reasons
            return BackendDecision(backend, eligible, tuple(reasons), 1.0 if eligible else 0.0)

        if backend == "container":
            if not caps.supports("isolation", "container_runtime"):
                reasons.append("container_runtime_unavailable")
            if spec.policy.allow_privileged and not caps.supports("isolation", "privileged_container"):
                reasons.append("privileged_mode_unavailable")
            eligible = not reasons
            return BackendDecision(backend, eligible, tuple(reasons), 0.90 if eligible else 0.0)

        if backend == "microvm":
            if not caps.supports("virtualization", "microvm"):
                reasons.append("microvm_unavailable")
            eligible = not reasons
            return BackendDecision(backend, eligible, tuple(reasons), 0.80 if eligible else 0.0)

        # A full VM is the strongest fallback and is intentionally selected last.
        if not caps.supports("virtualization", "vm"):
            reasons.append("vm_unavailable")
        eligible = not reasons
        return BackendDecision(backend, eligible, tuple(reasons), 0.70 if eligible else 0.0)
