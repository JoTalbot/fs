from __future__ import annotations

import pytest

from fs_overlay.metadata_redundancy import MetadataCorruption, MetadataRedundancy, MetadataReplica


def test_metadata_replicas_are_deterministic_and_verified() -> None:
    redundancy = MetadataRedundancy(replica_count=3)
    replicas = redundancy.create({"z": "last", "a": "first"})

    assert len(replicas) == 3
    assert {replica.digest for replica in replicas}.__len__() == 1
    assert redundancy.verify(replicas) == {"a": "first", "z": "last"}


def test_metadata_replica_payload_mutation_is_detected() -> None:
    redundancy = MetadataRedundancy()
    replicas = list(redundancy.create({"key": "value"}))
    replicas[1] = MetadataReplica(replicas[1].replica_id, replicas[1].digest, b'{"key":"tampered"}')

    with pytest.raises(MetadataCorruption, match="mismatch"):
        redundancy.verify(replicas)


def test_metadata_replica_digest_mutation_is_detected() -> None:
    redundancy = MetadataRedundancy()
    replicas = list(redundancy.create({"key": "value"}))
    replicas[0] = MetadataReplica(replicas[0].replica_id, "0" * 64, replicas[0].payload)

    with pytest.raises(MetadataCorruption, match="digest verification"):
        redundancy.verify(replicas)


@pytest.mark.parametrize("count", [0, 1, True, -1])
def test_metadata_redundancy_rejects_invalid_replica_count(count: object) -> None:
    with pytest.raises(ValueError):
        MetadataRedundancy(replica_count=count)  # type: ignore[arg-type]


def test_metadata_redundancy_requires_multiple_replicas() -> None:
    redundancy = MetadataRedundancy()
    replicas = redundancy.create({"key": "value"})

    with pytest.raises(MetadataCorruption, match="at least two"):
        redundancy.verify(replicas[:1])
