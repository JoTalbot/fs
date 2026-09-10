from fs_overlay.federation_protocol import FederationEnvelope
from fs_overlay.federation_state import DurableFederationState


def message(sequence: int, message_id: str) -> FederationEnvelope:
    return FederationEnvelope("node-a", message_id, "OBSERVE", sequence, 1, {"x": sequence})


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
