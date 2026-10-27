"""P1 Abstention and Impossibility Governor Use Case (PROD-P1).

Zero infrastructure imports; depends strictly on domain ports and Result monad.
Binds the 4-label termination partition (TERMINATED, OUT_OF_FUEL, IMPOSSIBLE,
INVALID_REQUEST) and optional coarsest-congruence quotient compression
(REV-SMRM-P1-QUOTIENT) to pfp.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from ..domain.kernel.result import DomainError, RefusalCode, Result


class AbstentionGovernorPort(Protocol):
    """Port for certified progress solving, congruence quotient compression, and budget abstention."""

    def evaluate_arena(
        self,
        raw_graph: Mapping[str, Any],
        initial: str,
        targets: tuple[str, ...],
        budget: str,
        *,
        task_id: str = "pfp-abstention-governor",
        compress_quotient: bool = True,
    ) -> dict[str, Any]: ...


class EvaluateAbstentionGovernorUseCase:
    """Evaluates bounded-budget reachability and impossibility with proof-carrying receipts."""

    def __init__(self, governor: AbstentionGovernorPort) -> None:
        self._governor = governor

    def execute(
        self,
        raw_graph: Mapping[str, Any],
        initial: str,
        targets: tuple[str, ...],
        budget: str,
        *,
        task_id: str = "pfp-abstention-governor",
        compress_quotient: bool = True,
    ) -> Result[dict[str, Any], DomainError]:
        if not raw_graph or not isinstance(initial, str) or not initial.strip():
            return Result.err(
                DomainError(
                    code=RefusalCode.TYPING_VIOLATION,
                    message="raw_graph must be non-empty and initial state must be a non-empty string",
                )
            )
        try:
            verdict = self._governor.evaluate_arena(
                raw_graph,
                initial,
                targets,
                budget,
                task_id=task_id,
                compress_quotient=compress_quotient,
            )
            if not verdict.get("certificate_accepted", False):
                return Result.err(
                    DomainError(
                        code=RefusalCode.GATE_REJECTED,
                        message=str(verdict.get("refusal_reason", "Certificate rejected by checker")),
                    )
                )
            return Result.ok(verdict)
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.GATE_REJECTED,
                    message=f"Abstention governor evaluation failed: {exc}",
                )
            )
