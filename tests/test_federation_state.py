import concurrent.futures
import multiprocessing
from contextlib import nullcontext
import os

from fs_overlay.durable_coordination import FileAdmissionCoordinator
from fs_overlay.federation_protocol import FederationEnvelope
from fs_overlay.federation_state import DurableFederationState


def message(sequence: int, message_id: str, sender: str = "node-a") -> FederationEnvelope:
    return FederationEnvelope(sender, message_id, "OBSERVE", sequence, 1, {"x": sequence})


def test_federation_state_persists_accepted_messages(tmp_path) -> None:
    path = tmp_path / "events.journal"
    state = DurableFederationState(path)
    assert state.accept(message(1, "m1"))
    assert not state.accept(message(1, "m2"))
    assert not state.accept(message(1, "m1"))
    assert state.accept(message(2, "m2"))

    restored = DurableFederationState(path)
    snapshot = restored.snapshot()
    assert snapshot.last_sequence == {"node-a": 2}
    assert snapshot.seen_message_ids == frozenset({"m1", "m2"})


def test_federation_state_restores_multiple_senders(tmp_path) -> None:
    path = tmp_path / "events.journal"
    state = DurableFederationState(path)
    assert state.accept(message(1, "a1", "node-a"))
    assert state.accept(message(1, "b1", "node-b"))
    assert state.accept(message(2, "a2", "node-a"))

    restored = DurableFederationState(path)
    assert restored.snapshot().last_sequence == {"node-a": 2, "node-b": 1}
    assert not restored.accept(message(1, "a3", "node-a"))
    assert restored.accept(message(2, "b2", "node-b"))


def test_thread_serialization_accepts_only_one_duplicate_sequence(tmp_path) -> None:
    state = DurableFederationState(tmp_path / "events.journal")
    envelope = message(1, "m1")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(state.accept, [envelope] * 8))
    assert results.count(True) == 1
    assert results.count(False) == 7
    assert state.snapshot().last_sequence == {"node-a": 1}


def test_coordinator_wraps_admission_and_journal_write(tmp_path) -> None:
    class RecordingCoordinator:
        def __init__(self) -> None:
            self.resources: list[str] = []
            self.entered = 0
            self.exited = 0

        def acquire(self, resource_id: str):
            self.resources.append(resource_id)
            owner = self

            class Guard:
                def __enter__(self):
                    owner.entered += 1
                    return None

                def __exit__(self, exc_type, exc, tb):
                    owner.exited += 1
                    return False

            return Guard()

    coordinator = RecordingCoordinator()
    state = DurableFederationState(tmp_path / "events.journal", coordinator=coordinator)
    assert state.accept(message(1, "m1"))
    assert coordinator.resources == ["federation-events"]
    assert coordinator.entered == 1
    assert coordinator.exited == 1


def test_coordinator_context_is_released_when_admission_fails(tmp_path) -> None:
    class RecordingCoordinator:
        def __init__(self) -> None:
            self.entered = 0
            self.exited = 0

        def acquire(self, resource_id: str):
            assert resource_id == "federation-events"
            owner = self

            class Guard:
                def __enter__(self):
                    owner.entered += 1
                    return None

                def __exit__(self, exc_type, exc, tb):
                    owner.exited += 1
                    return False

            return Guard()

    coordinator = RecordingCoordinator()
    state = DurableFederationState(tmp_path / "events.journal", coordinator=coordinator)
    assert not state.accept(message(-1, "invalid"))
    assert coordinator.entered == 1
    assert coordinator.exited == 1


def test_default_state_does_not_require_coordinator(tmp_path) -> None:
    state = DurableFederationState(tmp_path / "events.journal")
    assert state.accept(message(1, "m1"))


def test_coordinator_contract_shape() -> None:
    class Coordinator:
        def acquire(self, resource_id: str):
            assert resource_id == "federation-events"
            return nullcontext()

    coordinator = Coordinator()
    with coordinator.acquire("federation-events"):
        pass


def _accept_with_file_coordinator(path: str, locks: str, message_id: str, result: multiprocessing.Queue) -> None:
    state = DurableFederationState(path, coordinator=FileAdmissionCoordinator(locks, timeout=5))
    result.put(state.accept(message(1, message_id)))


def test_coordinated_processes_refresh_stale_admission_state(tmp_path) -> None:
    state_path = str(tmp_path / "events.journal")
    locks_path = str(tmp_path / "locks")
    ctx = multiprocessing.get_context("spawn")
    result = ctx.Queue()
    first = ctx.Process(target=_accept_with_file_coordinator, args=(state_path, locks_path, "m1", result))
    second = ctx.Process(target=_accept_with_file_coordinator, args=(state_path, locks_path, "m2", result))
    first.start()
    second.start()
    first.join(timeout=10)
    second.join(timeout=10)
    assert first.exitcode == 0
    assert second.exitcode == 0
    assert sorted(result.get(timeout=5) for _ in range(2)) == [False, True]

    restored = DurableFederationState(state_path)
    assert restored.snapshot().last_sequence == {"node-a": 1}
    assert restored.snapshot().seen_message_ids == frozenset({"m1"}) or restored.snapshot().seen_message_ids == frozenset({"m2"})


def test_ambiguous_journal_write_is_resolved_from_durable_state(tmp_path) -> None:
    """A post-write failure is resolved by restart, not by guessing in memory."""
    path = tmp_path / "events.journal"
    state = DurableFederationState(path)
    original_emit = state.events.emit

    def emit_then_fail(*args, **kwargs):
        original_emit(*args, **kwargs)
        raise OSError("simulated acknowledgement loss after durable append")

    state.events.emit = emit_then_fail
    try:
        try:
            state.accept(message(1, "ambiguous"))
        except OSError:
            pass
        else:
            raise AssertionError("simulated durable acknowledgement loss must surface")
    finally:
        state.events.emit = original_emit

    assert state.snapshot().seen_message_ids == frozenset()
    restored = DurableFederationState(path)
    assert restored.snapshot().last_sequence == {"node-a": 1}
    assert restored.snapshot().seen_message_ids == frozenset({"ambiguous"})
    assert not restored.accept(message(1, "retry"))
    assert restored.accept(message(2, "retry"))


def _crash_after_coordinated_append(path: str, locks: str, ready: multiprocessing.Event) -> None:
    state = DurableFederationState(path, coordinator=FileAdmissionCoordinator(locks, timeout=5))
    with state._coordinator.acquire(state.RESOURCE_ID):
        state.events.emit(
            "federation.accepted",
            details={
                "sender_node": "node-a",
                "message_id": "crash-ambiguous",
                "message_type": "OBSERVE",
                "sequence": 1,
                "digest": message(1, "crash-ambiguous").digest(),
            },
        )
        ready.set()
        os._exit(23)


def test_coordinated_admission_recovers_after_process_crash(tmp_path) -> None:
    """A crash after durable append leaves the journal authoritative and releases the lock."""
    state_path = str(tmp_path / "events.journal")
    locks_path = str(tmp_path / "locks")
    ctx = multiprocessing.get_context("spawn")
    ready = ctx.Event()
    process = ctx.Process(target=_crash_after_coordinated_append, args=(state_path, locks_path, ready))
    process.start()
    assert ready.wait(5)
    process.join(timeout=5)
    assert process.exitcode == 23

    restored = DurableFederationState(state_path, coordinator=FileAdmissionCoordinator(locks_path, timeout=1))
    assert restored.snapshot().last_sequence == {"node-a": 1}
    assert restored.snapshot().seen_message_ids == frozenset({"crash-ambiguous"})
    assert not restored.accept(message(1, "retry-after-crash"))
    assert restored.accept(message(2, "next-after-crash"))
