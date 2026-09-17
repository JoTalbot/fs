"""Platform wall-clock and monotonic/logical time primitives."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Callable


class PlatformTimeAdapter:
    """Provide UTC wall time and monotonic nanoseconds through narrow hooks."""

    def wall_time_ns(self) -> int:
        return time.time_ns()

    def wall_time(self) -> datetime:
        return datetime.fromtimestamp(self.wall_time_ns() / 1_000_000_000, tz=timezone.utc)

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()


@dataclass(slots=True)
class LogicalClock:
    """A monotonic logical clock that never moves backwards."""

    _value: int = 0
    _source: Callable[[], int] = time.monotonic_ns

    def now(self) -> int:
        observed = self._source()
        if type(observed) is not int or observed < 0:
            raise ValueError("logical clock source must return a non-negative integer")
        if observed > self._value:
            self._value = observed
        return self._value

    def observe(self, value: int) -> int:
        if type(value) is not int or value < 0:
            raise ValueError("logical clock value must be a non-negative integer")
        if value > self._value:
            self._value = value
        return self._value
