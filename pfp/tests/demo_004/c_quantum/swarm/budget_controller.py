"""Budget Controller for the Adversary Quantum Swarm (C021).

Enforces execution cost constraints:
- Hard ceiling: <= $0.25 per execution.
- Target preference: < $0.05 per execution.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List


class BudgetExhaustedRefusal(Exception):
    """Refusal raised when an execution exceeds the authorized monetary ceiling."""

    def __init__(self, message: str, current_cost: Decimal, ceiling: Decimal) -> None:
        super().__init__(f"{message} (cost={current_cost}, ceiling={ceiling})")
        self.current_cost = current_cost
        self.ceiling = ceiling


@dataclass(frozen=True)
class CostEntry:
    operation_id: str
    model_or_solver: str
    input_tokens: int
    output_tokens: int
    billed_cost_usd: Decimal
    timestamp_utc: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.operation_id == other.operation_id
            and self.model_or_solver == other.model_or_solver
            and self.input_tokens == other.input_tokens
            and self.output_tokens == other.output_tokens
            and self.billed_cost_usd == other.billed_cost_usd
            and self.timestamp_utc == other.timestamp_utc
        )


@dataclass
class CostLedger:
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_billed_cost_usd: Decimal = Decimal("0.00000")
    entries: List[CostEntry] = field(default_factory=list)

    def record(
        self,
        op_id: str,
        solver_name: str,
        inp: int,
        outp: int,
        cost: Decimal,
        timestamp: str,
    ) -> None:
        self.total_input_tokens += inp
        self.total_output_tokens += outp
        self.total_billed_cost_usd += cost
        self.entries.append(
            CostEntry(
                operation_id=op_id,
                model_or_solver=solver_name,
                input_tokens=inp,
                output_tokens=outp,
                billed_cost_usd=cost,
                timestamp_utc=timestamp,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "authority_effect": "None",
            "cost_basis": "SYNTHETIC_ESTIMATE",
            "billing_verified": False,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_billed_cost_usd": str(self.total_billed_cost_usd),
            "entry_count": len(self.entries),
            "entries": [
                {
                    "operation_id": e.operation_id,
                    "model_or_solver": e.model_or_solver,
                    "input_tokens": e.input_tokens,
                    "output_tokens": e.output_tokens,
                    "billed_cost_usd": str(e.billed_cost_usd),
                    "timestamp_utc": e.timestamp_utc,
                }
                for e in self.entries
            ],
        }


class BudgetController:
    """Guards execution against exceeding monetary limits."""

    def __init__(
        self,
        hard_ceiling_usd: Decimal = Decimal("0.25"),
        target_budget_usd: Decimal = Decimal("0.05"),
    ) -> None:
        self.hard_ceiling_usd = hard_ceiling_usd
        self.target_budget_usd = target_budget_usd
        self.ledger = CostLedger()

    @property
    def current_cost(self) -> Decimal:
        return self.ledger.total_billed_cost_usd

    @property
    def is_within_target(self) -> bool:
        return self.current_cost < self.target_budget_usd

    def charge(
        self,
        op_id: str,
        solver_name: str,
        inp_tokens: int,
        outp_tokens: int,
        rate_per_1k_input: Decimal = Decimal("0.0001"),
        rate_per_1k_output: Decimal = Decimal("0.0002"),
        timestamp_utc: str = "",
    ) -> Decimal:
        """Calculates and charges cost for an operation; raises refusal if ceiling exceeded."""
        cost = (Decimal(inp_tokens) / Decimal(1000) * rate_per_1k_input) + (
            Decimal(outp_tokens) / Decimal(1000) * rate_per_1k_output
        )

        projected = self.current_cost + cost
        if projected > self.hard_ceiling_usd:
            raise BudgetExhaustedRefusal(
                "Execution aborted: hard monetary budget ceiling exceeded",
                current_cost=projected,
                ceiling=self.hard_ceiling_usd,
            )

        self.ledger.record(
            op_id=op_id,
            solver_name=solver_name,
            inp=inp_tokens,
            outp=outp_tokens,
            cost=cost,
            timestamp=timestamp_utc or datetime.now(timezone.utc).isoformat(),
        )
        return cost
