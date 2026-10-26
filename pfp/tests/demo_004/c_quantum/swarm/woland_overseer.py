"""Compatibility entrypoint for C021 swarm requests.

C021 has no binding to the city's execution boundary in this PR. Refuse the
request without simulating a local bout or publishing execution artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

from .budget_controller import BudgetController
from .q40_solver import Q40Certificate, Q40StabilizerSolver

if TYPE_CHECKING:
    from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost


@dataclass(frozen=True)
class WolandQuantumSwarmResult:
    task_key: str
    verdict: str
    certificate: Q40Certificate
    billed_cost_usd: Decimal
    is_within_target_budget: bool
    output_directory: Path
    receipt_sha256: str
    refusal_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_effect": "None",
            "billed_cost_usd": str(self.billed_cost_usd),
            "cost_basis": "NO_EXECUTION",
            "billing_verified": False,
            "is_within_target_budget": self.is_within_target_budget,
            "output_directory": str(self.output_directory),
            "receipt_sha256": self.receipt_sha256,
            "task_key": self.task_key,
            "verdict": self.verdict,
            "refusal_code": self.refusal_code,
        }


class WolandQuantumOverseer:
    """Preserve the caller API while refusing an unbound the city execution."""

    def __init__(
        self,
        repo_root: Path,
        budget_ceiling: Decimal = Decimal("0.25"),
        host: RustSymbolGameHost | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.budget_controller = BudgetController(hard_ceiling_usd=budget_ceiling)
        self._host = host
        self.solver = Q40StabilizerSolver()

    def get_host(self) -> RustSymbolGameHost:
        if self._host is not None:
            return self._host
        from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost

        return RustSymbolGameHost()

    def execute_challenge(
        self,
        challenge_id: str,
        case_data: Mapping[str, Any],
        task_key: str | None = None,
        adversarial_zero_claim: bool = False,
    ) -> WolandQuantumSwarmResult:
        """Refuse until C021 is bound to the existing the city execution path."""
        refusal_code = "WOLAND_EXECUTION_UNAVAILABLE"
        eff_task_key = task_key or f"unexecuted_{challenge_id.lower()}"
        certificate = Q40Certificate(
            case_id=str(case_data.get("id") or case_data.get("case_id") or "unnamed"),
            status="UNKNOWN",
            energy=None,
            degeneracy=None,
            basis=[],
            decomposition=[],
            minimizers=[],
            witness=None,
            refusal_code=refusal_code,
            algebraic_verified=False,
            dense_verified=False,
        )
        return WolandQuantumSwarmResult(
            task_key=eff_task_key,
            verdict="REFUSE",
            certificate=certificate,
            billed_cost_usd=Decimal("0"),
            is_within_target_budget=True,
            output_directory=self.repo_root / "_ic/darpa/woland" / "runs" / eff_task_key,
            receipt_sha256="",
            refusal_code=refusal_code,
        )
