import json

import pytest

from fs_overlay.event_log import EventLog


def test_event_log_reload_continues_sequence_and_causal_chain(tmp_path) -> None:
    path = tmp_path / "events.log"
    first = EventLog(path)
    first_event = first.emit("admission.accepted", object_id="obj-1")

    second = EventLog(path)
    second.reload()
    second_event = second.emit("execution.authorized", object_id="obj-1")

    events = list(second.replay())
    assert [event["sequence"] for event in events] == [1, 2]
    assert second_event["payload"]["sequence"] == 2
    assert second_event["payload"]["causal_parent"] == first_event["payload"]["event_hash"]


def test_event_log_rejects_tampered_event_payload(tmp_path) -> None:
    path = tmp_path / "events.log"
    log = EventLog(path)
    log.emit("admission.accepted", object_id="obj-1")

    raw = path.read_bytes().splitlines()
    record = json.loads(raw[0][16:])
    record["payload"]["object_id"] = "tampered"
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    path.write_bytes(f"{len(encoded):016x}".encode() + encoded + b"\n")

    with pytest.raises(ValueError, match="event hash verification failed"):
        list(EventLog(path).replay())


def test_event_log_rejects_sequence_gap(tmp_path) -> None:
    path = tmp_path / "events.log"
    log = EventLog(path)
    log.emit("first")
    log.emit("second")

    raw = path.read_bytes().splitlines()
    records = [json.loads(line[16:]) for line in raw]
    records[1]["payload"]["sequence"] = 3
    body = records[1]["payload"]
    body.pop("event_hash", None)
    import hashlib
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    records[1]["payload"]["event_hash"] = hashlib.sha256(canonical).hexdigest()
    encoded = json.dumps(records[1], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    path.write_bytes(
        f"{len(json.dumps(records[0], sort_keys=True, separators=(\",\", \":\"), ensure_ascii=False).encode()):016x}".encode()
        + json.dumps(records[0], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        + b"\n"
        + f"{len(encoded):016x}".encode()
        + encoded
        + b"\n"
    )

    with pytest.raises(ValueError, match="event sequence verification failed"):
        list(EventLog(path).replay())
