import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

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


def test_event_log_rejects_schema_coercion_and_missing_integrity(tmp_path) -> None:
    path = tmp_path / "events.log"
    log = EventLog(path)
    record = log.emit("first")

    malformed = json.loads(json.dumps(record))
    malformed["payload"]["sequence"] = "1"
    path.write_bytes(_encode(malformed))
    with pytest.raises(ValueError, match="event sequence is invalid"):
        list(EventLog(path).replay())

    malformed = json.loads(json.dumps(record))
    malformed["payload"]["event_hash"] = None
    path.write_bytes(_encode(malformed))
    with pytest.raises(ValueError, match="event event_hash is invalid"):
        list(EventLog(path).replay())


def test_event_log_rejects_unexpected_event_fields(tmp_path) -> None:
    path = tmp_path / "events.log"
    log = EventLog(path)
    record = log.emit("first")
    record["payload"]["unexpected"] = True
    path.write_bytes(_encode(record))

    with pytest.raises(ValueError, match="event schema verification failed"):
        list(EventLog(path).replay())


def test_event_log_rejects_invalid_optional_and_timestamp_types(tmp_path) -> None:
    path = tmp_path / "events.log"
    log = EventLog(path)
    record = log.emit("first")

    malformed = json.loads(json.dumps(record))
    malformed["payload"]["causal_parent"] = 1
    path.write_bytes(_encode(malformed))
    with pytest.raises(ValueError, match="event causal_parent is invalid"):
        list(EventLog(path).replay())

    malformed = json.loads(json.dumps(record))
    malformed["payload"]["timestamp_ns"] = True
    path.write_bytes(_encode(malformed))
    with pytest.raises(ValueError, match="event timestamp_ns is invalid"):
        list(EventLog(path).replay())


def test_event_log_concurrent_emit_is_serialized(tmp_path) -> None:
    path = tmp_path / "events.log"
    log = EventLog(path)

    with ThreadPoolExecutor(max_workers=16) as executor:
        records = list(executor.map(lambda i: log.emit(f"event-{i}"), range(16)))

    sequences = sorted(int(record["payload"]["sequence"]) for record in records)
    assert sequences == list(range(1, 17))

    events = list(log.replay())
    assert [event["sequence"] for event in events] == list(range(1, 17))
    for previous, current in zip(events, events[1:]):
        assert current["causal_parent"] == previous["event_hash"]


def test_event_log_append_failure_does_not_consume_sequence(tmp_path, monkeypatch) -> None:
    path = tmp_path / "events.log"
    log = EventLog(path)
    original_append = log._journal.append
    calls = 0

    def failing_append(operation, payload):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("injected append failure")
        return original_append(operation, payload)

    monkeypatch.setattr(log._journal, "append", failing_append)
    with pytest.raises(OSError, match="injected append failure"):
        log.emit("failed")

    record = log.emit("recovered")
    assert record["payload"]["sequence"] == 1
    assert record["payload"]["causal_parent"] is None
    assert [event["sequence"] for event in log.replay()] == [1]
