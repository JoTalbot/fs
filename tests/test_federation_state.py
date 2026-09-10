import concurrent.futures
from contextlib import nullcontext

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
