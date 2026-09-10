import pytest

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


def test_replay_rejects_duplicate_message_id(tmp_path) -> None:
    path = tmp_path / "events.journal"
    state = DurableFederationState(path)
    assert state.accept(message(1, "m1"))
    assert state.accept(message(2, "m2"))
    with path.open("ab") as handle:
        original = path.read_bytes().splitlines()[0]
        handle.write(original + b"\n")
    with pytest.raises(ValueError, match="event sequence verification failed"):
        DurableFederationState(path)


def test_thread_serialization_accepts_only_one_duplicate_sequence(tmp_path) -> None:
    import concurrent.futures

    state = DurableFederationState(tmp_path / "events.journal")
    envelope = message(1, "m1")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(state.accept, [envelope] * 8))
    assert results.count(True) == 1
    assert results.count(False) == 7
    assert state.snapshot().last_sequence == {"node-a": 1}
