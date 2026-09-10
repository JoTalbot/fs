from fs_overlay.model import (
    CapabilitySet,
    CapabilityValue,
    EnvironmentSpec,
    ObjectRecord,
    ObjectState,
    ObjectType,
)


def test_object_generation_advances_on_state_change() -> None:
    record = ObjectRecord(type=ObjectType.WORKSPACE, name="demo")
    assert record.generation == 0
    generation = record.advance(ObjectState.READY)
    assert generation == 1
    assert record.state is ObjectState.READY
    assert record.ref().generation == 1


def test_unknown_capability_is_not_supported() -> None:
    caps = CapabilitySet(
        platform="test",
        architecture="x86_64",
        isolation={"container_runtime": CapabilityValue.unknown()},
    )
    assert not caps.supports("isolation", "container_runtime")


def test_environment_spec_has_conservative_defaults() -> None:
    spec = EnvironmentSpec(name="demo")
    assert spec.policy.runtime == "auto"
    assert spec.policy.network == "deny"
    assert spec.restart == "on-failure"
