import hashlib
import json

import pytest

from fs_overlay.event_log import EventLog


def _encode(record: dict[str, object]) -> bytes:
    body = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return f"{len(body):016x}".encode() + body + b"\n"


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

    record = next(iter(EventLog(path)._journal.replay()))
    record["payload"]["object_id"] = "tampered"
    path.write_bytes(_encode(record))

    with pytest.raises(ValueError, match="event hash verification failed"):
        list(EventLog(path).replay())


def test_event_log_rejects_sequence_gap(tmp_path) -> None:
    path = tmp_path / "events.log"
    log = EventLog(path)
    log.emit("first")
    log.emit("second")

    records = list(EventLog(path)._journal.replay())
    records[1]["payload"]["sequence"] = 3
    body = dict(records[1]["payload"])
    body.pop("event_hash", None)
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    records[1]["payload"]["event_hash"] = hashlib.sha256(canonical).hexdigest()
    path.write_bytes(b"".join(_encode(record) for record in records))

    with pytest.raises(ValueError, match="event sequence verification failed"):
        list(EventLog(path).replay())
