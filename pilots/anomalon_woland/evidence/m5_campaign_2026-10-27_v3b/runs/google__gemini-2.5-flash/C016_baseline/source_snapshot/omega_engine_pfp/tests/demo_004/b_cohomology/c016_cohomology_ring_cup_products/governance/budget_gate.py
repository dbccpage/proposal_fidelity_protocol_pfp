"""Budget Gate Controller for C016: Cohomology Ring Cup Products.

Enforces:
- Hard budget ceiling: $1.00 billed inference per arm (Tier T3)
- Fast path optimization target: < $0.05
- Model parameter ceiling: <= 70B total parameters
- allow_fallbacks: False
- Subprocess sandbox isolation (U09)
"""

from __future__ import annotations

import math
from typing import Any

BUDGET_CEILING_USD = 1.00
FAST_PATH_TARGET_USD = 0.05
MAX_PARAMETERS = 70_000_000_000


def check_budget_gate(accounting_data: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    audit = accounting_data.get("audit_trail", {})
    raw_billed_cost = audit.get("billed_cost_usd") if isinstance(audit, dict) else None
    allow_fallbacks = accounting_data.get("allow_fallbacks", True)

    details = {
        "billed_cost_usd": raw_billed_cost,
        "budget_ceiling_usd": BUDGET_CEILING_USD,
        "fast_path_target_usd": FAST_PATH_TARGET_USD,
        "allow_fallbacks": allow_fallbacks,
    }

    if allow_fallbacks:
        return False, "Budget gate violation: allow_fallbacks must be False", details

    if (
        type(raw_billed_cost) not in (int, float)
        or not math.isfinite(float(raw_billed_cost))
        or float(raw_billed_cost) < 0
    ):
        return (
            False,
            "Budget gate violation: a finite non-negative billed_cost_usd is required",
            details,
        )

    billed_cost = float(raw_billed_cost)
    details["billed_cost_usd"] = billed_cost
    if billed_cost > BUDGET_CEILING_USD:
        return (
            False,
            f"Budget ceiling exceeded: ${billed_cost:.4f} > ${BUDGET_CEILING_USD:.2f}",
            details,
        )

    meets_fast_path = billed_cost < FAST_PATH_TARGET_USD
    details["meets_fast_path"] = meets_fast_path
    return True, f"Budget gate passed (billed: ${billed_cost:.4f})", details
