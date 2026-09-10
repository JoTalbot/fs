"""FS-IR: a small, backend-neutral intermediate representation.

FS-IR is descriptive. It can validate intent and plans, but it never grants
authority and never performs host-side operations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class IRKind(StrEnum):
    INTENT = "intent"
    REQUIREMENT = "requirement"
    PLAN = "plan"
    TRANSACTION = "transaction"
    EXECUTION = "execution"
    OBSERVATION = "observation"


@dataclass(frozen=True, slots=True)
class CapabilityRequirement:
    name: str
    minimum: int | float | None = None
    unit: str = ""
    optional: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.name:
            errors.append("capability requirement missing name")
        if self.minimum is not None and self.minimum < 0:
            errors.append(f"{self.name}: minimum cannot be negative")
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class ResourceRequirement:
    name: str
    amount: int | float
    unit: str

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.name:
            errors.append("resource requirement missing name")
        if self.amount < 0:
            errors.append(f"{self.name}: amount cannot be negative")
        if not self.unit:
            errors.append(f"{self.name}: missing unit")
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class SemanticIR:
    kind: IRKind
    ir_id: str
    operation: str
    targets: tuple[str, ...] = ()
    capabilities: tuple[CapabilityRequirement, ...] = ()
    resources: tuple[ResourceRequirement, ...] = ()
    authority_scope: str = ""
    policy_constraints: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_effects: tuple[str, ...] = ()
    verification: tuple[str, ...] = ()

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.ir_id:
            errors.append("missing ir id")
        if not self.operation:
            errors.append("missing operation")
        if self.kind is not IRKind.INTENT and not self.targets:
            errors.append("non-intent IR requires target")
        if self.kind in {IRKind.PLAN, IRKind.TRANSACTION, IRKind.EXECUTION} and not self.verification:
            errors.append(f"{self.kind.value} requires verification conditions")
        for item in self.capabilities:
            errors.extend(item.validate())
        for item in self.resources:
            errors.extend(item.validate())
        if len(set(self.dependencies)) != len(self.dependencies):
            errors.append("duplicate dependency")
        return tuple(errors)
