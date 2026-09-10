import hashlib

from fs_overlay.replication import ReplicaAction, ReplicaExecutor


class MemoryAdapter:
    def __init__(self, values=None):
        self.values = dict(values or {})
        self.writes = []

    def read(self, node_id, object_id):
        return self.values[(node_id, object_id)]

    def write(self, node_id, object_id, data):
        self.writes.append((node_id, object_id, data))
        self.values[(node_id, object_id)] = data


def action(data=b"payload"):
    return ReplicaAction("obj", "source", "target", hashlib.sha256(data).hexdigest())


def test_executor_verifies_source_and_target() -> None:
    data = b"payload"
    adapter = MemoryAdapter({("source", "obj"): data})
    result = ReplicaExecutor(adapter).execute(action(data))
    assert result.status == "SUCCEEDED"
    assert result.observed_sha256 == action(data).expected_sha256
    assert adapter.values[("target", "obj")] == data


def test_executor_does_not_copy_bad_source() -> None:
    adapter = MemoryAdapter({("source", "obj"): b"tampered"})
    result = ReplicaExecutor(adapter).execute(action(b"payload"))
    assert result.status == "FAILED"
    assert "source integrity" in result.reason
    assert adapter.writes == []


class CorruptingAdapter(MemoryAdapter):
    def write(self, node_id, object_id, data):
        self.writes.append((node_id, object_id, data))
        self.values[(node_id, object_id)] = b"corrupt"


def test_executor_detects_corrupt_target() -> None:
    data = b"payload"
    adapter = CorruptingAdapter({("source", "obj"): data})
    result = ReplicaExecutor(adapter).execute(action(data))
    assert result.status == "FAILED"
    assert "target verification" in result.reason
