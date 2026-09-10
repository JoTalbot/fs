from fs_overlay.model import CapabilitySet, CapabilityValue, EnvironmentSpec, ExecutionPolicy
from fs_overlay.planner import BackendPlanner


def test_auto_prefers_native_when_policy_allows_it() -> None:
    caps = CapabilitySet(platform="linux", architecture="x86_64")
    spec = EnvironmentSpec(name="demo", policy=ExecutionPolicy(runtime="auto"))
    decision = BackendPlanner().select(spec, caps)
    assert decision.backend == "native"
    assert decision.eligible


def test_auto_selects_container_for_stronger_network_policy() -> None:
    caps = CapabilitySet(
        platform="linux",
        architecture="x86_64",
        isolation={"container_runtime": CapabilityValue.yes()},
    )
    spec = EnvironmentSpec(
        name="demo",
        policy=ExecutionPolicy(runtime="auto", network="isolated"),
    )
    decision = BackendPlanner().select(spec, caps)
    assert decision.backend == "container"


def test_explicit_vm_fails_when_unavailable() -> None:
    caps = CapabilitySet(platform="linux", architecture="x86_64")
    spec = EnvironmentSpec(name="demo", policy=ExecutionPolicy(runtime="vm"))
    decision = BackendPlanner().select(spec, caps)
    assert not decision.eligible
    assert decision.backend is None
    assert "vm_unavailable" in decision.reasons
