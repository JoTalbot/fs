import json
import multiprocessing
from pathlib import Path

import pytest

from fs_overlay.authority_revocation import AuthorityRevocationRegistry, RevocationRecord


def _revoke_in_process(path: str, authority_id: str, result) -> None:
    try:
        registry = AuthorityRevocationRegistry(path, coordination_timeout=5)
        record = registry.revoke(authority_id, reason="concurrent test")
        result.put(("ok", record.sequence, record.authority_id))
    except Exception as exc:  # pragma: no cover - surfaced through the queue
        result.put(("error", type(exc).__name__, str(exc)))


def test_revocation_is_durable_and_survives_reopen(tmp_path: Path) -> None:
    path = tmp_path / "revocations.log"
    registry = AuthorityRevocationRegistry(path)
    record = registry.revoke("authority-1", reason="manual cancellation")

    reopened = AuthorityRevocationRegistry(path)
    assert reopened.is_revoked("authority-1") is True
    assert reopened.records() == (record,)


def test_revocation_rejects_duplicate_authority(tmp_path: Path) -> None:
    registry = AuthorityRevocationRegistry(tmp_path / "revocations.log")
    registry.revoke("authority-1", reason="cancelled")
    with pytest.raises(ValueError, match="already revoked"):
        registry.revoke("authority-1", reason="again")


def test_revocation_replay_rejects_tampered_event(tmp_path: Path) -> None:
    path = tmp_path / "revocations.log"
    registry = AuthorityRevocationRegistry(path)
    registry.revoke("authority-1", reason="cancelled")
    line = path.read_text(encoding="utf-8")
    path.write_text(line.replace("cancelled", "tampered"), encoding="utf-8")
    with pytest.raises(ValueError, match="event digest mismatch"):
        AuthorityRevocationRegistry(path)


def test_revocation_replay_rejects_noncanonical_field_types(tmp_path: Path) -> None:
    path = tmp_path / "revocations.log"
    record = RevocationRecord.create(
        sequence=1,
        authority_id="authority-1",
        reason="cancelled",
        previous_digest="0" * 64,
    )
    data = json.loads(record.to_line())

    for field, value in {
        "sequence": True,
        "authority_id": 1,
        "reason": 1,
        "previous_digest": 1,
        "event_digest": 1,
    }.items():
        malformed = dict(data)
        malformed[field] = value
        path.write_text(json.dumps(malformed) + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="malformed revocation record"):
            AuthorityRevocationRegistry(path)


def test_revocation_replay_rejects_unknown_fields(tmp_path: Path) -> None:
    path = tmp_path / "revocations.log"
    record = RevocationRecord.create(
        sequence=1,
        authority_id="authority-1",
        reason="cancelled",
        previous_digest="0" * 64,
    )
    data = json.loads(record.to_line())
    data["unexpected"] = "ignored"
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="malformed revocation record"):
        AuthorityRevocationRegistry(path)


def test_revocation_replay_rejects_duplicate_top_level_field_before_schema_validation(tmp_path: Path) -> None:
    path = tmp_path / "revocations.log"
    registry = AuthorityRevocationRegistry(path)
    registry.revoke("authority-1", reason="cancelled")
    line = path.read_text(encoding="utf-8").strip()
    duplicate = line.replace('"sequence":1}', '"sequence":1,"sequence":1}', 1)
    assert duplicate != line
    path.write_text(duplicate + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="malformed revocation record"):
        AuthorityRevocationRegistry(path)


def test_revocation_replay_rejects_duplicate_nested_field_before_digest_validation(tmp_path: Path) -> None:
    path = tmp_path / "revocations.log"
    registry = AuthorityRevocationRegistry(path)
    registry.revoke("authority-1", reason="cancelled")
    line = path.read_text(encoding="utf-8").strip()
    duplicate = line.replace(
        '"authority_id":"authority-1","event_digest"',
        '"authority_id":"authority-1","authority_id":"authority-1","event_digest"',
        1,
    )
    assert duplicate != line
    path.write_text(duplicate + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="malformed revocation record"):
        AuthorityRevocationRegistry(path)


def test_revocation_replay_rejects_chain_break(tmp_path: Path) -> None:
    path = tmp_path / "revocations.log"
    registry = AuthorityRevocationRegistry(path)
    first = registry.revoke("authority-1", reason="cancelled")
    second = RevocationRecord.create(
        sequence=2,
        authority_id="authority-2",
        reason="cancelled",
        previous_digest="0" * 64,
    )
    path.write_text(first.to_line() + "\n" + second.to_line() + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash-chain break"):
        AuthorityRevocationRegistry(path)


def test_revocation_replay_rejects_sequence_discontinuity(tmp_path: Path) -> None:
    path = tmp_path / "revocations.log"
    first = RevocationRecord.create(
        sequence=2,
        authority_id="authority-1",
        reason="cancelled",
        previous_digest="0" * 64,
    )
    path.write_text(first.to_line() + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sequence discontinuity"):
        AuthorityRevocationRegistry(path)


def test_revocation_serializes_concurrent_writers(tmp_path: Path) -> None:
    path = str(tmp_path / "revocations.log")
    ctx = multiprocessing.get_context("spawn")
    result = ctx.Queue()
    processes = [
        ctx.Process(target=_revoke_in_process, args=(path, f"authority-{index}", result))
        for index in (1, 2)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(15)

    assert all(process.exitcode == 0 for process in processes)
    outcomes = [result.get(timeout=2) for _ in processes]
    assert all(outcome[0] == "ok" for outcome in outcomes), outcomes
    assert sorted(outcome[1] for outcome in outcomes) == [1, 2]

    reopened = AuthorityRevocationRegistry(path)
    assert [record.sequence for record in reopened.records()] == [1, 2]
    assert {record.authority_id for record in reopened.records()} == {
        "authority-1",
        "authority-2",
    }
