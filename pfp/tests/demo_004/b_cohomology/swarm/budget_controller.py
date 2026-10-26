"""Budget Controller for the Woland Cohomology Swarm.

Enforces execution cost constraints:
- Hard ceiling: <= $0.25 per execution.
- Target preference: < $0.05 per execution.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
        timestamp_utc: str,
    ) -> None:
        self.total_input_tokens += inp
        self.total_output_tokens += outp
        self.total_billed_cost_usd += cost
        self.entries.append(CostEntry(op_id, solver_name, inp, outp, cost, timestamp_utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_billed_cost_usd": str(self.total_billed_cost_usd),
            "entries_count": len(self.entries),
        }


class BudgetController:
    """Oversees and limits execution expenditure for the Woland Swarm."""

    HARD_CEILING_USD = Decimal("0.25")
    TARGET_CEILING_USD = Decimal("0.05")

    def __init__(
        self,
        hard_ceiling_usd: Decimal = HARD_CEILING_USD,
        target_ceiling_usd: Decimal = TARGET_CEILING_USD,
    ) -> None:
        self.hard_ceiling = hard_ceiling_usd
        self.target_ceiling = target_ceiling_usd
        self.ledger = CostLedger()

    def charge(
        self,
        op_id: str,
        solver_name: str,
        inp_tokens: int,
        outp_tokens: int,
        rate_per_1k_input: Decimal = Decimal("0.0000"),
        rate_per_1k_output: Decimal = Decimal("0.0000"),
        fixed_cost: Decimal = Decimal("0.0000"),
        timestamp_utc: str = "",
    ) -> Decimal:
        """Compute and charge cost for an operation, enforcing ceilings."""
        token_cost = (Decimal(inp_tokens) / Decimal(1000)) * rate_per_1k_input + (
            Decimal(outp_tokens) / Decimal(1000)
        ) * rate_per_1k_output
        op_cost = token_cost + fixed_cost
        projected = self.ledger.total_billed_cost_usd + op_cost

        if projected > self.hard_ceiling:
            raise BudgetExhaustedRefusal(
                "HARD_BUDGET_CEILING_EXCEEDED",
                current_cost=projected,
                ceiling=self.hard_ceiling,
            )

        self.ledger.record(op_id, solver_name, inp_tokens, outp_tokens, op_cost, timestamp_utc)
        return op_cost

    def is_within_target(self) -> bool:
        """Return True if total expenditure is strictly within the target (< $0.05)."""
        return self.ledger.total_billed_cost_usd < self.target_ceiling

    @property
    def total_cost(self) -> Decimal:
        return self.ledger.total_billed_cost_usd

    def to_accounting_dict(
        self, provider: str = "local_rust_seam", model_id: str = "omega_solvers_v1"
    ) -> dict[str, Any]:
        """Format accounting data matching C011 and U06 provenance standards."""
        return {
            "schema_version": "omega.accounting.v1",
            "provider": provider,
            "model_id": model_id,
            "hard_ceiling_usd": str(self.hard_ceiling),
            "target_ceiling_usd": str(self.target_ceiling),
            "total_input_tokens": self.ledger.total_input_tokens,
            "total_output_tokens": self.ledger.total_output_tokens,
            "total_billed_cost_usd": str(self.ledger.total_billed_cost_usd),
            "within_target": self.is_within_target(),
            "records": [
                {
                    "operation_id": e.operation_id,
                    "solver": e.model_or_solver,
                    "input_tokens": e.input_tokens,
                    "output_tokens": e.output_tokens,
                    "billed_cost_usd": str(e.billed_cost_usd),
                    "timestamp_utc": e.timestamp_utc,
                }
                for e in self.ledger.entries
            ],
        }

    def write_accounting_json(
        self, path: Any, provider: str = "local_rust_seam", model_id: str = "omega_solvers_v1"
    ) -> Any:
        import json
        from pathlib import Path

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_accounting_dict(provider=provider, model_id=model_id)
        p.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        return p
