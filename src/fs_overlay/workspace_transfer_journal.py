"""Durable intent journal for future workspace transfer execution.

This module records authority-boundary state only. It never mutates a workspace
or deletes source data. A future materializer must treat the journal as a
precondition and provide its own transactional filesystem implementation.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .workspace_migration import WorkspaceTransfer, WorkspaceTransferPlan


@dataclass(frozen=True, slots=True)
class TransferJournalEntry:
    transaction_id: str
    phase: str
    operation: WorkspaceTransfer
    snapshot_id: str
    source_workspace_id: str
    destination_workspace_id: str | None

    def as_record(self) -> dict[str, object]:
        return {
            "version": 1,
            "transaction_id": self.transaction_id,
            "phase": self.phase,
            "operation": self.operation.value,
            "snapshot_id": self.snapshot_id,
            "source_workspace_id": self.source_workspace_id,
            "destination_workspace_id": self.destination_workspace_id,
        }


class TransferJournalCorruption(ValueError):
    """Raised when a non-tail journal record cannot be trusted."""


class WorkspaceTransferJournal:
    """Append-only transfer intent journal with fail-closed replay."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def begin(self, plan: WorkspaceTransferPlan) -> str:
        if not plan.ready:
            raise ValueError("cannot journal a transfer plan that is not ready")
        transaction_id = uuid.uuid4().hex
        self._append(
            TransferJournalEntry(
                transaction_id,
                "prepared",
                plan.operation,
                plan.snapshot_id,
                plan.source_workspace_id,
                plan.destination_workspace_id,
            )
        )
        return transaction_id

    def mark(self, transaction_id: str, plan: WorkspaceTransferPlan, phase: str) -> None:
        if not transaction_id or not phase:
            raise ValueError("transaction_id and phase are required")
        if not plan.ready:
            raise ValueError("cannot advance an unready transfer plan")
        self._append(
            TransferJournalEntry(
                transaction_id,
                phase,
                plan.operation,
                plan.snapshot_id,
                plan.source_workspace_id,
                plan.destination_workspace_id,
            )
        )

    def replay(self) -> Iterator[TransferJournalEntry]:
        if not self.path.exists():
            return
        with self.path.open("rb") as handle:
            while True:
                line = handle.readline()
                if not line:
                    return
                if not line.endswith(b"\n"):
                    if handle.peek(1):
                        raise TransferJournalCorruption("journal contains a malformed non-tail record")
                    return
                try:
                    raw = json.loads(line[:-1])
                    result = TransferJournalEntry(
                        str(raw["transaction_id"]),
                        str(raw["phase"]),
                        WorkspaceTransfer(str(raw["operation"])),
                        str(raw["snapshot_id"]),
                        str(raw["source_workspace_id"]),
                        None if raw.get("destination_workspace_id") is None else str(raw["destination_workspace_id"]),
                    )
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise TransferJournalCorruption("journal record is invalid") from exc
                if raw.get("version") != 1:
                    raise TransferJournalCorruption("unsupported journal version")
                yield result

    def _append(self, entry: TransferJournalEntry) -> None:
        encoded = json.dumps(entry.as_record(), sort_keys=True, separators=(",", ":")).encode()
        with self.path.open("ab") as handle:
            handle.write(encoded + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
