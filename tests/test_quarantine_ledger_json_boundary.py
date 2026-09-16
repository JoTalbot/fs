from __future__ import annotations

from pathlib import Path

import pytest

from fs_overlay.storage_resilience import QuarantineLedger


def _append_raw(path: Path, body: bytes) -> None:
    with path.open("ab") as handle:
        handle.write(f"{len(body):016x}".encode() + body + b"\n")


def test_quarantine_replay_rejects_duplicate_top_level_field_before_schema_validation(tmp_path: Path) -> None:
    path = tmp_path / "quarantine.log"
    ledger = QuarantineLedger(path)
    ledger.quarantine("carrier-a", reason="bad hash")
    body = (
        b'{"carrier_id":"carrier-a","expected_hash":null,"observed_hash":null,'
        b'"reason":"bad hash","record_id":"record-1","timestamp_ns":1,'
        b'"timestamp_ns":1}'
    )
    _append_raw(path, body)

    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        ledger.replay()


def test_quarantine_replay_rejects_duplicate_nested_object_field_before_schema_validation(tmp_path: Path) -> None:
    path = tmp_path / "quarantine.log"
    ledger = QuarantineLedger(path)
    ledger.quarantine("carrier-a", reason="bad hash")
    body = (
        b'{"carrier_id":"carrier-a","expected_hash":null,"observed_hash":null,'
        b'"reason":"bad hash","record_id":"record-1","timestamp_ns":1,'
        b'"carrier_id":"carrier-a"}'
    )
    _append_raw(path, body)

    with pytest.raises(ValueError, match="quarantine ledger corruption"):
        ledger.replay()
