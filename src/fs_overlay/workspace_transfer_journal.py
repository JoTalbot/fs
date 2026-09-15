"""Durable intent journal for future workspace transfer execution.

This module records authority-boundary state only. It never mutates a workspace
or deletes source data. A future materializer must treat the journal as a
precondition and provide its own transactional filesystem implementation.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator

from .workspace_migration import WorkspaceTransfer, WorkspaceTransferPlan


class TransferJournalPhase(str, Enum):
    PREPARED = "prepared"
    MATERIALIZING = "materializing"
    COMMITTED = "committed"
    ABORTED = "aborted"


@dataclass(frozen=True, slots=True)
class TransferJournalEntry:
    transaction_id: str
    phase: TransferJournalPhase
    operation: WorkspaceTransfer
    snapshot_id: str
    source_workspace_id: str
    destination_workspace_id: str | None

    def as_record(self) -> dict[str, object]:
        return {
            "version": 2,
            "transaction_id": self.transaction_id,
            "phase": self.phase.value,
            "operation": self.operation.value,
            "snapshot_id": self.snapshot_id,
            "source_workspace_id": self.source_workspace_id,
            "destination_workspace_id": self.destination_workspace_id,
        }


class TransferJournalCorruption(ValueError):
    """Raised when a journal record cannot be trusted."""


class WorkspaceTransferJournal:
    """Append-only transfer intent journal with fail-closed replay."""

    _TRANSITIONS: dict[TransferJournalPhase, frozenset[TransferJournalPhase]] = {
        TransferJournalPhase.PREPARED: frozenset(
            {TransferJournalPhase.MATERIALIZING, TransferJournalPhase.ABORTED}
        ),
        TransferJournalPhase.MATERIALIZING: frozenset(
            {TransferJournalPhase.COMMITTED, TransferJournalPhase.ABORTED}
        ),
        TransferJournalPhase.COMMITTED: frozenset(),
        TransferJournalPhase.ABORTED: frozenset(),
    }

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
                TransferJournalPhase.PREPARED,
                plan.operation,
                plan.snapshot_id,
                plan.source_workspace_id,
                plan.destination_workspace_id,
            )
        )
        return transaction_id

    def mark(
        self,
        transaction_id: str,
        plan: WorkspaceTransferPlan,
        phase: TransferJournalPhase | str,
    ) -> None:
        if not transaction_id:
            raise ValueError("transaction_id is required")
        if not plan.ready:
            raise ValueError("cannot advance an unready transfer plan")
        try:
            next_phase = TransferJournalPhase(phase)
        except ValueError as exc:
            raise ValueError("unknown transfer journal phase") from exc

        entries = list(self.replay())
        current = next(
            (entry for entry in reversed(entries) if entry.transaction_id == transaction_id),
            None,
        )
        if current is None:
            raise ValueError("unknown transfer transaction")
        self._validate_identity(current, transaction_id, plan)
        if next_phase not in self._TRANSITIONS[current.phase]:
            raise ValueError(
                f"invalid transfer journal transition: {current.phase.value} -> {next_phase.value}"
            )
        self._append(
            TransferJournalEntry(
                transaction_id,
                next_phase,
                plan.operation,
                plan.snapshot_id,
                plan.source_workspace_id,
                plan.destination_workspace_id,
            )
        )

    def recovery_candidates(self) -> tuple[TransferJournalEntry, ...]:
        """Return transfers left in materializing state after a crash."""
        latest: dict[str, TransferJournalEntry] = {}
        for entry in self.replay():
            latest[entry.transaction_id] = entry
        return tuple(
            entry for entry in latest.values() if entry.phase is TransferJournalPhase.MATERIALIZING
        )

    def replay(self) -> Iterator[TransferJournalEntry]:
        if not self.path.exists():
            return
        latest: dict[str, TransferJournalEntry] = {}
        expected_digest: str | None = None
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
                except json.JSONDecodeError as exc:
                    raise TransferJournalCorruption("journal record is invalid") from exc
                if raw.get("version") != 2:
                    raise TransferJournalCorruption("unsupported journal version")
                digest = raw.get("event_digest")
                previous_digest = raw.get("previous_digest")
                if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                    raise TransferJournalCorruption("journal event digest is invalid")
                if previous_digest != expected_digest:
                    raise TransferJournalCorruption("journal hash chain is broken")
                unsigned = dict(raw)
                unsigned["event_digest"] = None
                encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
                if hashlib.sha256(encoded).hexdigest() != digest:
                    raise TransferJournalCorruption("journal event digest mismatch")
                try:
                    result = TransferJournalEntry(
                        str(raw["transaction_id"]),
                        TransferJournalPhase(str(raw["phase"])),
                        WorkspaceTransfer(str(raw["operation"])),
                        str(raw["snapshot_id"]),
                        str(raw["source_workspace_id"]),
                        None if raw.get("destination_workspace_id") is None else str(raw["destination_workspace_id"]),
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise TransferJournalCorruption("journal record is invalid") from exc
                previous = latest.get(result.transaction_id)
                if previous is not None:
                    try:
                        self._validate_identity(previous, result.transaction_id, result)
                    except ValueError as exc:
                        raise TransferJournalCorruption("journal transaction identity changed") from exc
                    if result.phase not in self._TRANSITIONS[previous.phase]:
                        raise TransferJournalCorruption(
                            f"invalid journal transition: {previous.phase.value} -> {result.phase.value}"
                        )
                elif result.phase is not TransferJournalPhase.PREPARED:
                    raise TransferJournalCorruption("journal transaction does not begin with prepared")
                latest[result.transaction_id] = result
                expected_digest = digest
                yield result

    @staticmethod
    def _validate_identity(
        current: TransferJournalEntry,
        transaction_id: str,
        plan_or_entry: WorkspaceTransferPlan | TransferJournalEntry,
    ) -> None:
        if current.transaction_id != transaction_id:
            raise ValueError("transaction identity mismatch")
        if (
            current.operation != plan_or_entry.operation
            or current.snapshot_id != plan_or_entry.snapshot_id
            or current.source_workspace_id != plan_or_entry.source_workspace_id
            or current.destination_workspace_id != plan_or_entry.destination_workspace_id
        ):
            raise ValueError("transfer transaction identity mismatch")

    def _append(self, entry: TransferJournalEntry) -> None:
        unsigned = entry.as_record()
        unsigned["previous_digest"] = self._last_digest()
        unsigned["event_digest"] = None
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        unsigned["event_digest"] = hashlib.sha256(encoded).hexdigest()
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        with self.path.open("ab") as handle:
            handle.write(encoded + b"\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _last_digest(self) -> str | None:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return None
        last: str | None = None
        with self.path.open("rb") as handle:
            for line in handle:
                if not line.endswith(b"\n"):
                    raise TransferJournalCorruption("journal contains a malformed non-tail record")
                try:
                    raw = json.loads(line[:-1])
                except json.JSONDecodeError as exc:
                    raise TransferJournalCorruption("journal record is invalid") from exc
                digest = raw.get("event_digest")
                if not isinstance(digest, str):
                    raise TransferJournalCorruption("journal event digest is invalid")
                last = digest
        return last
