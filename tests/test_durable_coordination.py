import multiprocessing
import os
import time

import pytest

from fs_overlay.durable_coordination import CoordinationTimeout, FileAdmissionCoordinator


def test_file_coordinator_serializes_same_resource(tmp_path) -> None:
    coordinator = FileAdmissionCoordinator(tmp_path / "locks", timeout=0.05)
    with coordinator.acquire("federation-events"):
        with pytest.raises(CoordinationTimeout):
            coordinator.acquire("federation-events")


def test_file_coordinator_allows_different_resources(tmp_path) -> None:
    coordinator = FileAdmissionCoordinator(tmp_path / "locks", timeout=0.05)
    with coordinator.acquire("a"):
        with coordinator.acquire("b"):
            pass


def test_file_coordinator_releases_after_context_exit(tmp_path) -> None:
    coordinator = FileAdmissionCoordinator(tmp_path / "locks", timeout=0.05)
    with coordinator.acquire("federation-events"):
        pass
    with coordinator.acquire("federation-events"):
        pass


def test_file_coordinator_rejects_invalid_configuration(tmp_path) -> None:
    with pytest.raises(ValueError):
        FileAdmissionCoordinator(tmp_path, timeout=-1)
    with pytest.raises(ValueError):
        FileAdmissionCoordinator(tmp_path, poll_interval=0)
    coordinator = FileAdmissionCoordinator(tmp_path)
    with pytest.raises(ValueError):
        coordinator.acquire("")


def _hold_lock(path: str, ready: multiprocessing.Event, release: multiprocessing.Event) -> None:
    coordinator = FileAdmissionCoordinator(path, timeout=1)
    with coordinator.acquire("federation-events"):
        ready.set()
        release.wait(2)


def _crash_with_lock(path: str, ready: multiprocessing.Event) -> None:
    coordinator = FileAdmissionCoordinator(path, timeout=1)
    with coordinator.acquire("federation-events"):
        ready.set()
        os._exit(17)


def test_file_coordinator_serializes_across_processes(tmp_path) -> None:
    ctx = multiprocessing.get_context("spawn")
    ready = ctx.Event()
    release = ctx.Event()
    process = ctx.Process(target=_hold_lock, args=(str(tmp_path / "locks"), ready, release))
    process.start()
    try:
        assert ready.wait(5)
        coordinator = FileAdmissionCoordinator(tmp_path / "locks", timeout=0.05)
        started = time.monotonic()
        with pytest.raises(CoordinationTimeout):
            coordinator.acquire("federation-events")
        assert time.monotonic() - started >= 0.04
    finally:
        release.set()
        process.join(timeout=5)
        if process.is_alive():
            process.terminate()
        assert process.exitcode == 0


def test_file_coordinator_lock_is_released_after_process_crash(tmp_path) -> None:
    ctx = multiprocessing.get_context("spawn")
    ready = ctx.Event()
    process = ctx.Process(target=_crash_with_lock, args=(str(tmp_path / "locks"), ready))
    process.start()
    assert ready.wait(5)
    process.join(timeout=5)
    assert process.exitcode == 17

    coordinator = FileAdmissionCoordinator(tmp_path / "locks", timeout=0.2)
    with coordinator.acquire("federation-events"):
        pass
