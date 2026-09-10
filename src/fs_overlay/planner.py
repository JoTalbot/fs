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
    """Select the least powerful backend that actually enforces the policy.

    Unknown enforcement support never counts as support. A backend is eligible
    only when its declared semantics cover every requested constraint.
    """

    ORDER = ("native", "container", "microvm", "vm")

    def plan(self, spec: EnvironmentSpec, caps: CapabilitySet) -> tuple[BackendDecision, ...]:
        requested = spec.policy.runtime
        candidates = (requested,) if requested != "auto" else self.ORDER
        return tuple(self._evaluate(backend, spec, caps) for backend in candidates)

    def select(self, spec: EnvironmentSpec, caps: CapabilitySet) -> BackendDecision:
        decisions = self.plan(spec, caps)
        eligible = [d for d in decisions if d.eligible]
        if not eligible:
            return BackendDecision(None, False, tuple(r for d in decisions for r in d.reasons))
        return max(eligible, key=lambda d: (d.score, -self.ORDER.index(d.backend)))

    @staticmethod
    def _portable_constraints(spec: EnvironmentSpec) -> list[str]:
        policy = spec.policy
        reasons: list[str] = []
        if policy.filesystem != "host":
            reasons.append("filesystem_isolation_required")
        if policy.network != "host":
            reasons.append("network_policy_requires_isolation")
        if policy.devices:
            reasons.append("device_policy_requires_isolation")
        if policy.allow_privileged:
            reasons.append("privileged_execution_requires_explicit_backend")
        if policy.resources.cpu_millis is not None:
            reasons.append("cpu_limit_requires_resource_controller")
        if policy.resources.memory_bytes is not None:
            reasons.append("memory_limit_requires_resource_controller")
        if policy.resources.pids is not None:
            reasons.append("pid_limit_requires_resource_controller")
        return reasons

    def _evaluate(self, backend: str, spec: EnvironmentSpec, caps: CapabilitySet) -> BackendDecision:
        if backend not in self.ORDER:
            return BackendDecision(backend, False, ("unsupported_backend",))

        if backend == "native":
            reasons = self._portable_constraints(spec)
            return BackendDecision(backend, not reasons, tuple(reasons), 1.0 if not reasons else 0.0)

        if backend == "container":
            reasons: list[str] = []
            if not caps.supports("isolation", "container_runtime"):
                reasons.append("container_runtime_unavailable")
            if spec.policy.allow_privileged and not caps.supports("isolation", "privileged_container"):
                reasons.append("privileged_mode_unavailable")
            if spec.policy.devices:
                reasons.append("device_policy_requires_device_aware_container")
            if spec.policy.resources.cpu_millis is not None or spec.policy.resources.memory_bytes is not None or spec.policy.resources.pids is not None:
                if not caps.supports("isolation", "resource_controller"):
                    reasons.append("resource_controller_unavailable")
            return BackendDecision(backend, not reasons, tuple(reasons), 0.90 if not reasons else 0.0)

        if backend == "microvm":
            reasons = []
            if not caps.supports("virtualization", "microvm"):
                reasons.append("microvm_unavailable")
            return BackendDecision(backend, not reasons, tuple(reasons), 0.80 if not reasons else 0.0)

        reasons = []
        if not caps.supports("virtualization", "vm"):
            reasons.append("vm_unavailable")
        return BackendDecision(backend, not reasons, tuple(reasons), 0.70 if not reasons else 0.0)
