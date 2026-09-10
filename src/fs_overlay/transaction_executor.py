"""Transaction-aware execution boundary for the FS reference runtime.

Planning, execution, verification and commit are deliberately separate.
Concrete backends provide preparation and compensation hooks; this layer
never invents evidence for boundaries that a backend did not verify.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .adapter import ProcessResult
from .execution_coordinator import ExecutionBoundaryPlan
from .verification import VerificationCheck, VerificationResult, verify


@dataclass(frozen=True, slots=True)
class ExecutionTransaction:
    transaction_id: str
    state: str
    result: ProcessResult | None = None
    verification: VerificationResult | None = None
    reasons: tuple[str, ...] = ()


Executor = Callable[..., ProcessResult]
Prepare = Callable[[ExecutionBoundaryPlan], object]
Abort = Callable[[object], None]


class TransactionExecutor:
    """Execute an admitted plan through prepare, execute, verify and commit."""

    def execute(
        self,
        transaction_id: str,
        plan: ExecutionBoundaryPlan,
        argv: tuple[str, ...],
        executor: Executor,
        *,
        checks: tuple[VerificationCheck, ...] = (),
        evidence_provider: Callable[[VerificationCheck], object] | None = None,
        prepare: Prepare | None = None,
        abort: Abort | None = None,
    ) -> ExecutionTransaction:
        if not transaction_id:
            raise ValueError("transaction_id is required")
        if not plan.admitted:
            return ExecutionTransaction(transaction_id, "rejected", None, None, plan.reasons or ("execution_not_admitted",))

        prepared = None
        try:
            if prepare is not None:
                prepared = prepare(plan)
            result = executor(argv=argv, admitted=True)
        except Exception as exc:
            if prepared is not None and abort is not None:
                try:
                    abort(prepared)
                except Exception:
                    pass
            return ExecutionTransaction(transaction_id, "failed", None, None, (f"executor_error:{type(exc).__name__}",))

        if result.status != "succeeded":
            if prepared is not None and abort is not None:
                try:
                    abort(prepared)
                except Exception:
                    pass
            return ExecutionTransaction(transaction_id, "failed", result, None, ("execution_failed",))

        if checks:
            if evidence_provider is None:
                if prepared is not None and abort is not None:
                    abort(prepared)
                return ExecutionTransaction(transaction_id, "verification_failed", result, None, ("verification_provider_required",))
            verification = verify(checks, evidence_provider)  # type: ignore[arg-type]
            if not verification.verified:
                if prepared is not None and abort is not None:
                    try:
                        abort(prepared)
                    except Exception:
                        pass
                return ExecutionTransaction(transaction_id, "verification_failed", result, verification, verification.reasons)
        else:
            verification = None

        return ExecutionTransaction(transaction_id, "committed", result, verification)
