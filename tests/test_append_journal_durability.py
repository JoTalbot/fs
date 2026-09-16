from pathlib import Path

import fs_overlay.storage_engine as storage_engine
from fs_overlay.storage_engine import AppendJournal


def test_append_journal_persists_parent_directory_entry(tmp_path, monkeypatch) -> None:
    calls: list[Path] = []

    def record_directory_sync(directory: str | Path) -> None:
        calls.append(Path(directory))

    monkeypatch.setattr(storage_engine, "_fsync_directory", record_directory_sync)

    journal = AppendJournal(tmp_path / "events.log")
    journal.append("event", {"value": "durable"})

    assert calls == [tmp_path]
    assert list(journal.replay())[0]["payload"] == {"value": "durable"}
