"""Deterministic, opt-in failure injection for resilience tests.

Failure injection is deliberately explicit and inert until a caller supplies an
injector. It is a test/qualification aid, not an authority or recovery policy.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class InjectedFailure(RuntimeError):
    """A deterministic test failure requested at a named injection point."""


@dataclass(slots=True)
class FailureInjector:
    """Trigger named failures a deterministic number of times.

    ``arm(point, count=n)`` makes the next ``n`` checkpoints at that point fail.
    The configuration is local to the injector and has no process-global state.
    """

    _remaining: dict[str, int] = field(default_factory=dict)

    def arm(self, point: str, *, count: int = 1) -> None:
        if not isinstance(point, str) or not point:
            raise ValueError("failure injection point must be a non-empty string")
        if type(count) is not int or count <= 0:
            raise ValueError("failure injection count must be a positive integer")
        self._remaining[point] = count

    def disarm(self, point: str) -> None:
        if not isinstance(point, str) or not point:
            raise ValueError("failure injection point must be a non-empty string")
        self._remaining.pop(point, None)

    def checkpoint(self, point: str) -> None:
        if not isinstance(point, str) or not point:
            raise ValueError("failure injection point must be a non-empty string")
        remaining = self._remaining.get(point, 0)
        if remaining <= 0:
            return
        if remaining == 1:
            del self._remaining[point]
        else:
            self._remaining[point] = remaining - 1
        raise InjectedFailure(f"injected failure at {point}")

    def pending(self, point: str) -> int:
        if not isinstance(point, str) or not point:
            raise ValueError("failure injection point must be a non-empty string")
        return self._remaining.get(point, 0)
