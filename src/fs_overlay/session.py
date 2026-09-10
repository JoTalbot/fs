"""Logical application sessions independent of execution location."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class MobilityClass(StrEnum):
    FIXED = "fixed"
    CHECKPOINTABLE = "checkpointable"
    RESTARTABLE = "restartable"
    STATELESS = "stateless"
    DEVICE_BOUND = "device_bound"


class SessionState(StrEnum):
    CREATED = "created"
    ADMITTED = "admitted"
    RUNNING = "running"
    PAUSED = "paused"
    MIGRATING = "migrating"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(slots=True)
class ApplicationSession:
    session_id: str
    application_id: str
    principal_id: str
    mobility: MobilityClass
    requirements: tuple[str, ...] = ()
    execution_node: str | None = None
    presentation_endpoint: str | None = None
    checkpoint_ref: str | None = None
    authority_scope: str = ""
    state: SessionState = SessionState.CREATED
    metadata: dict[str, str] = field(default_factory=dict)

    def bind_execution(self, node_id: str) -> None:
        if not node_id:
            raise ValueError("execution node id is required")
        self.execution_node = node_id
        self.state = SessionState.RUNNING

    def bind_presentation(self, endpoint_id: str) -> None:
        if not endpoint_id:
            raise ValueError("presentation endpoint id is required")
        self.presentation_endpoint = endpoint_id

    def can_migrate(self) -> bool:
        return self.mobility in {
            MobilityClass.CHECKPOINTABLE,
            MobilityClass.RESTARTABLE,
            MobilityClass.STATELESS,
        }

    def begin_migration(self) -> None:
        if not self.can_migrate():
            raise ValueError(f"session mobility class {self.mobility.value} is not migratable")
        self.state = SessionState.MIGRATING

    def fail(self) -> None:
        self.state = SessionState.FAILED
