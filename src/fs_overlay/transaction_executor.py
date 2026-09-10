"""Transaction-aware execution boundary for the FS reference runtime.

This layer enforces the ordering contract without pretending that planning is
enforcement. It prepares an admitted boundary plan, invokes an injected
executor, observes the result, and only reports a committed outcome after a
successful execution. Concrete Linux mount/cgroup setup remains behind the
executor boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .adapter import ProcessResult
from .execution_coordinator import ExecutionBoundaryPlan


@dataclass(frozen=True, slots=True)
class ExecutionTransaction:
    transaction_id: str
    state: str
    result: ProcessResult | None = None
    reasons: tuple[str, ...] = ()


Executor = Callable[..., ProcessResult]


class TransactionExecutor:
    """Run only an already-admitted execution boundary plan."""

    def execute(
        self,
        transaction_id: str,
        plan: ExecutionBoundaryPlan,
        argv: tuple[str, ...],
        executor: Executor,
    ) -> ExecutionTransaction:
        if not transaction_id:
            raise ValueError("transaction_id is required")
        if not plan.admitted:
            return ExecutionTransaction(
                transaction_id, "rejected", None, plan.reasons or ("execution_not_admitted",)
            )
        try:
            result = executor(argv=argv, admitted=True)
        except Exception as exc:
            return ExecutionTransaction(transaction_id, "failed", None, (f"executor_error:{type(exc).__name__}",))
        if result.status != "succeeded":
            return ExecutionTransaction(transaction_id, "failed", result, ("execution_failed",))
        return ExecutionTransaction(transaction_id, "committed", result)
