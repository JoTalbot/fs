from __future__ import annotations

import json
from itertools import permutations
from pathlib import Path

import pytest

from fs_overlay.storage_resilience import (
    CarrierState,
    QuarantineLedger,
    RecoveryGraph,
    RecoveryNode,
    SnapshotStore,
    recovery_state,
)


def test_recovery_graph_rejects_unknown_dependency() -> None:
    with pytest.raises(ValueError, match="unknown recovery dependency"):
        RecoveryGraph([RecoveryNode("publish", "obj", "publish", ("missing",))])


def test_recovery_graph_rejects_cycles() -> None:
    graph = RecoveryGraph()
    graph.add(RecoveryNode("a", "obj", "prepare", ()))
    graph.add(RecoveryNode("b", "obj", "publish", ("a",)))
    graph.nodes["a"] = RecoveryNode("a", "obj", "prepare", ("b",))
    with pytest.raises(ValueError, match="recovery graph contains a cycle"):
        graph.order()


def test_recovery_graph_order_is_deterministic() -> None:
    nodes = (
        RecoveryNode("publish", "obj", "publish", ("verify",)),
        RecoveryNode("verify", "obj", "verify", ("prepare",)),
        RecoveryNode("prepare", "obj", "prepare"),
        RecoveryNode("audit", "obj", "audit", ("prepare",)),
    )
    orders = {RecoveryGraph(order).order() for order in permutations(nodes)}
    assert orders == {("prepare", "audit", "verify", "publish")}


def test_placement_excludes_unapproved_unhealthy_and_under_capacity() -> None:
    carriers = (
        CarrierState("approved", "d1", 100, 10, True, True, 0.0),
        CarrierState("unapproved", "d2", 100, 10, True, False, 1.0),
        CarrierState("unhealthy", "d3", 100, 10, False, True, 1.0),
        CarrierState("small", "d4", 100, 99, True, True, 1.0),
    )
    from fs_overlay.storage_resilience import PlacementPlanner

    assert [c.carrier_id for c in PlacementPlanner().rank(carriers, required_bytes=10)] == ["approved"]


def test_placement_is_deterministic_and_honors_excluded_failure_domains() -> None:
    from fs_overlay.storage_resilience import PlacementPlanner

    carriers = (
        CarrierState("b", "d2", 100, 0, True, True, 0.5),
        CarrierState("a", "d1", 100, 0, True, True, 0.5),
    )
    planner = PlacementPlanner()
    assert tuple(c.carrier_id for c in planner.rank(carriers)) == ("b", "a")
    assert tuple(c.carrier_id for c in planner.rank(carriers, excluded_domains=("d2",))) == ("a", "b")


def test_snapshot_round_trip_preserves_valid_persisted_state(tmp_path: Path) -> None:
    store = SnapshotStore(tmp_path / "snapshots")
    snapshot = store.create((), generation=1, metadata={"source": "test"})

    assert store.get(snapshot.snapshot_id) == snapshot


def _snapshot_payload(tmp_path: Path) -> tuple[SnapshotStore, dict[str, object]]:
    store = SnapshotStore(tmp_path / "snapshots")
    snapshot = store.create((), generation=1, metadata={"source": "test"})
    return store, json.loads(snapshot.to_bytes())


def test_snapshot_rejects_boolean_numeric_fields(tmp_path: Path) -> None:
    from fs_overlay.storage_resilience import Snapshot

    _, payload = _snapshot_payload(tmp_path)
    payload["generation"] = True
    with pytest.raises(ValueError, match="invalid snapshot generation"):
        Snapshot.from_bytes(json.dumps(payload).encode())


def test_snapshot_rejects_coercible_identity_and_merkle_types(tmp_path: Path) -> None:
    from fs_overlay.storage_resilience import Snapshot

    _, payload = _snapshot_payload(tmp_path)
    payload["snapshot_id"] = 123
    with pytest.raises(ValueError, match="invalid snapshot id"):
        Snapshot.from_bytes(json.dumps(payload).encode())

    _, payload = _snapshot_payload(tmp_path)
    payload["merkle_root"] = 123
    with pytest.raises(ValueError, match="invalid snapshot object id"):
        Snapshot.from_bytes(json.dumps(payload).encode())


def test_snapshot_rejects_unexpected_fields(tmp_path: Path) -> None:
    from fs_overlay.storage_resilience import Snapshot

    _, payload = _snapshot_payload(tmp_path)
    payload["unexpected"] = "field"
    with pytest.raises(ValueError, match="snapshot fields are invalid"):
        Snapshot.from_bytes(json.dumps(payload).encode())


def test_snapshot_rejects_invalid_metadata_types(tmp_path: Path) -> None:
    from fs_overlay.storage_resilience import Snapshot

    _, payload = _snapshot_payload(tmp_path)
    payload["metadata"] = {"source": 1}
    with pytest.raises(ValueError, match="invalid snapshot metadata"):
        Snapshot.from_bytes(json.dumps(payload).encode())


def test_snapshot_rejects_non_list_objects(tmp_path: Path) -> None:
    from fs_overlay.storage_resilience import Snapshot

    _, payload = _snapshot_payload(tmp_path)
    payload["objects"] = {"not": "a-list"}
    with pytest.raises(ValueError, match="invalid snapshot objects"):
        Snapshot.from_bytes(json.dumps(payload).encode())


def test_quarantine_is_append_only_and_replay_preserves_evidence(tmp_path: Path) -> None:
    ledger = QuarantineLedger(tmp_path / "quarantine.log")
    first = ledger.quarantine("carrier-a", reason="unexpected hash", observed_hash="bad", expected_hash="good")
    second = ledger.quarantine("carrier-a", reason="still unexpected", observed_hash="worse", expected_hash="good")

    records = ledger.replay()
    assert [record.record_id for record in records] == [first.record_id, second.record_id]
    assert [record.reason for record in records] == ["unexpected hash", "still unexpected"]


def _quarantine_payload(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    ledger = QuarantineLedger(tmp_path / "quarantine.log")
    record = ledger.quarantine("carrier-a", reason="bad hash", observed_hash="bad", expected_hash="good")
    path = tmp_path / "quarantine.log"
    line = path.read_bytes().splitlines()[0]
    return path, json.loads(line[16:])


def test_quarantine_replay_rejects_coercible_types(tmp_path: Path) -> None:
    path, payload = _quarantine_payload(tmp_path)
    payload["carrier_id"] = 123
    path.write_bytes(f"{len(json.dumps(payload).encode()):016x}".encode() + json.dumps(payload).encode() + b"\n")
    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        QuarantineLedger(path).replay()

    path, payload = _quarantine_payload(tmp_path / "timestamp")
    payload["timestamp_ns"] = True
    body = json.dumps(payload).encode()
    path.write_bytes(f"{len(body):016x}".encode() + body + b"\n")
    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        QuarantineLedger(path).replay()

    path, payload = _quarantine_payload(tmp_path / "hash")
    payload["observed_hash"] = 123
    body = json.dumps(payload).encode()
    path.write_bytes(f"{len(body):016x}".encode() + body + b"\n")
    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        QuarantineLedger(path).replay()


def test_quarantine_replay_rejects_unexpected_and_missing_fields(tmp_path: Path) -> None:
    path, payload = _quarantine_payload(tmp_path)
    payload["unexpected"] = "field"
    body = json.dumps(payload).encode()
    path.write_bytes(f"{len(body):016x}".encode() + body + b"\n")
    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        QuarantineLedger(path).replay()

    path, payload = _quarantine_payload(tmp_path / "missing")
    del payload["record_id"]
    body = json.dumps(payload).encode()
    path.write_bytes(f"{len(body):016x}".encode() + body + b"\n")
    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        QuarantineLedger(path).replay()


def test_quarantine_replay_rejects_negative_timestamp(tmp_path: Path) -> None:
    path, payload = _quarantine_payload(tmp_path)
    payload["timestamp_ns"] = -1
    body = json.dumps(payload).encode()
    path.write_bytes(f"{len(body):016x}".encode() + body + b"\n")
    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        QuarantineLedger(path).replay()


def test_quarantine_replay_rejects_malformed_record(tmp_path: Path) -> None:
    path = tmp_path / "quarantine.log"
    ledger = QuarantineLedger(path)
    ledger.quarantine("carrier-a", reason="bad hash")
    with path.open("ab") as handle:
        body = b'{"corrupt":true}'
        handle.write(f"{len(body):016x}".encode() + body + b"\n")

    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        ledger.replay()


def test_quarantine_replay_rejects_length_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "quarantine.log"
    ledger = QuarantineLedger(path)
    ledger.quarantine("carrier-a", reason="bad hash")
    with path.open("ab") as handle:
        body = b'{}'
        handle.write(f"{len(body) + 1:016x}".encode() + body + b"\n")

    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        ledger.replay()


def test_quarantine_replay_rejects_truncated_frame(tmp_path: Path) -> None:
    path = tmp_path / "quarantine.log"
    ledger = QuarantineLedger(path)
    ledger.quarantine("carrier-a", reason="bad hash")
    with path.open("ab") as handle:
        handle.write(b"0000000000000010")

    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        ledger.replay()


def test_recovery_state_never_reports_success_below_data_threshold() -> None:
    assert recovery_state(1, 2) == "UNRECOVERABLE"
    assert recovery_state(2, 2, total_shards=3) == "DEGRADED"
    assert recovery_state(3, 2, total_shards=3) == "HEALTHY"
    assert recovery_state(3, 2, total_shards=3, repairing=True) == "REPAIRING"


def test_recovery_state_rejects_invalid_counts() -> None:
    with pytest.raises(ValueError):
        recovery_state(-1, 2)
    with pytest.raises(ValueError):
        recovery_state(2, 0)
    with pytest.raises(ValueError):
        recovery_state(4, 2, total_shards=3)
    with pytest.raises(ValueError):
        recovery_state(2, 3, total_shards=2)
