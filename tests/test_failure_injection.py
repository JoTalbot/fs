from __future__ import annotations

import pytest

from fs_overlay.failure_injection import FailureInjector, InjectedFailure


def test_failure_injection_is_inert_by_default() -> None:
    injector = FailureInjector()
    injector.checkpoint("storage.write")
    assert injector.pending("storage.write") == 0


def test_failure_injection_is_one_shot_and_deterministic() -> None:
    injector = FailureInjector()
    injector.arm("storage.write")

    with pytest.raises(InjectedFailure, match="storage.write"):
        injector.checkpoint("storage.write")
    injector.checkpoint("storage.write")
    assert injector.pending("storage.write") == 0


def test_failure_injection_supports_multiple_failures() -> None:
    injector = FailureInjector()
    injector.arm("storage.write", count=2)

    with pytest.raises(InjectedFailure):
        injector.checkpoint("storage.write")
    assert injector.pending("storage.write") == 1
    with pytest.raises(InjectedFailure):
        injector.checkpoint("storage.write")
    injector.checkpoint("storage.write")


def test_failure_injection_rearming_replaces_existing_budget() -> None:
    injector = FailureInjector()
    injector.arm("storage.write", count=3)
    injector.arm("storage.write", count=1)
    assert injector.pending("storage.write") == 1

    with pytest.raises(InjectedFailure):
        injector.checkpoint("storage.write")
    assert injector.pending("storage.write") == 0


def test_failure_injection_disarm_is_explicit() -> None:
    injector = FailureInjector()
    injector.arm("storage.write", count=3)
    injector.disarm("storage.write")
    injector.checkpoint("storage.write")
    assert injector.pending("storage.write") == 0


@pytest.mark.parametrize(
    "point,count",
    [("", 1), ("storage.write", 0), ("storage.write", -1), ("storage.write", True)],
)
def test_failure_injection_rejects_invalid_arm_arguments(point: str, count: int) -> None:
    with pytest.raises(ValueError):
        FailureInjector().arm(point, count=count)


@pytest.mark.parametrize("point", ["", 1, None])
def test_failure_injection_rejects_invalid_points(point: object) -> None:
    injector = FailureInjector()
    with pytest.raises(ValueError):
        injector.checkpoint(point)  # type: ignore[arg-type]
