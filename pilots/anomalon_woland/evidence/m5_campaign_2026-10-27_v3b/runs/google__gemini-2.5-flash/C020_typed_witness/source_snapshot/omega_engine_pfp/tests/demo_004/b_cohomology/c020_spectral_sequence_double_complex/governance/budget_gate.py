"""Budget Gate for C020: Fail-closed cost bounds."""

from __future__ import annotations

import math
from typing import Any

BUDGET_CEILING_USD = 2.00
OPTIMIZATION_TARGET_USD = 0.05


def verify_budget(accounting_data: dict[str, Any]) -> tuple[bool, str]:
    tier = accounting_data.get("tier")
    if tier != "T4":
        return False, f"Expected tier T4, got {tier}"

    raw_billed_cost = accounting_data.get("billed_cost_usd")
    if (
        type(raw_billed_cost) not in (int, float)
        or not math.isfinite(float(raw_billed_cost))
        or float(raw_billed_cost) < 0
    ):
        return False, "A finite non-negative billed_cost_usd is required"
    billed_cost = float(raw_billed_cost)
    if billed_cost > BUDGET_CEILING_USD:
        return False, f"Billed cost ${billed_cost:.4f} exceeds ceiling ${BUDGET_CEILING_USD:.2f}"

    if accounting_data.get("allow_fallbacks") is not False:
        return False, "allow_fallbacks must be explicitly False"

    return True, f"Budget verified: ${billed_cost:.4f} <= ${BUDGET_CEILING_USD:.2f}"
