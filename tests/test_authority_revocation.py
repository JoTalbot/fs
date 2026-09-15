from pathlib import Path

import pytest

from fs_overlay.authority_revocation import AuthorityRevocationRegistry, RevocationRecord


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
