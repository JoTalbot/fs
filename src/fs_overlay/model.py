"""Core platform-neutral data models for the FS control plane.

The models are intentionally dependency-free so they can be used by the CLI,
workers, adapters and future API implementations without importing host APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4


class ObjectState(str, Enum):
    NEW = "new"
    PROVISIONING = "provisioning"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    STOPPED = "stopped"
    DETACHED = "detached"
    QUARANTINED = "quarantined"


class ObjectType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"
    WORKSPACE = "workspace"
    VOLUME = "volume"
    CONTAINER = "container"
    PROCESS = "process"
    SERVICE = "service"
    ENVIRONMENT = "environment"
    SNAPSHOT = "snapshot"
    DEVICE = "device"
    NETWORK = "network"
    PACKAGE = "package"
    POLICY = "policy"


@dataclass(frozen=True, slots=True)
class ObjectRef:
    """Stable reference to a managed object generation."""

    id: UUID
    type: ObjectType
    generation: int = 0


@dataclass(slots=True)
class ObjectRecord:
    """Common state envelope shared by every managed object."""

    type: ObjectType
    name: str
    id: UUID = field(default_factory=uuid4)
    generation: int = 0
    state: ObjectState = ObjectState.NEW
    labels: dict[str, str] = field(default_factory=dict)
    policy_ref: ObjectRef | None = None
    snapshot_ref: ObjectRef | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def ref(self) -> ObjectRef:
        return ObjectRef(self.id, self.type, self.generation)

    def advance(self, state: ObjectState) -> int:
        """Advance to a new observable generation and return its number."""
        self.generation += 1
        self.state = state
        self.updated_at = datetime.now(timezone.utc)
        return self.generation


@dataclass(frozen=True, slots=True)
class ResourceBudget:
    """Optional execution constraints expressed in portable units."""

    cpu_millis: int | None = None
    memory_bytes: int | None = None
    disk_bytes: int | None = None
    pids: int | None = None


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    """Portable execution/isolation policy.

    The strings are semantic values. Platform adapters translate them to native
    mechanisms without leaking those mechanisms into the model.
    """

    runtime: str = "auto"
    filesystem: str = "workspace-only"
    network: str = "deny"
    devices: tuple[str, ...] = ()
    resources: ResourceBudget = field(default_factory=ResourceBudget)
    allow_privileged: bool = False


@dataclass(frozen=True, slots=True)
class EnvironmentSpec:
    """Declarative desired state for an executable FS environment."""

    name: str
    workspace: ObjectRef | None = None
    command: tuple[str, ...] = ()
    policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    restart: str = "on-failure"
    environment: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CapabilityValue:
    """A capability that can be true, false, unknown, or restricted."""

    value: str
    reason: str | None = None

    @classmethod
    def yes(cls, reason: str | None = None) -> "CapabilityValue":
        return cls("true", reason)

    @classmethod
    def no(cls, reason: str | None = None) -> "CapabilityValue":
        return cls("false", reason)

    @classmethod
    def unknown(cls, reason: str | None = None) -> "CapabilityValue":
        return cls("unknown", reason)

    @classmethod
    def restricted(cls, reason: str | None = None) -> "CapabilityValue":
        return cls("restricted", reason)


@dataclass(frozen=True, slots=True)
class CapabilitySet:
    """Normalized host/backend capabilities reported to the planner."""

    platform: str
    architecture: str
    filesystem: Mapping[str, Any] = field(default_factory=dict)
    execution: Mapping[str, CapabilityValue] = field(default_factory=dict)
    services: Mapping[str, CapabilityValue] = field(default_factory=dict)
    isolation: Mapping[str, CapabilityValue] = field(default_factory=dict)
    virtualization: Mapping[str, CapabilityValue] = field(default_factory=dict)
    resources: Mapping[str, int] = field(default_factory=dict)

    def supports(self, group: str, feature: str) -> bool:
        value = getattr(self, group, {}).get(feature)
        return isinstance(value, CapabilityValue) and value.value == "true"
