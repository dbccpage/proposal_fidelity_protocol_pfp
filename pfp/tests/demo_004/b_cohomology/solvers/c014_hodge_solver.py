"""Compatibility entrypoint for C014; execution belongs to the registered port."""

from __future__ import annotations

from typing import Any, Mapping

from pfp.domain.cohomology.solver import solve


def solve_c014(case: Mapping[str, Any], host: Any = None) -> dict[str, Any]:
    """Preserve the owning solver's result, including unavailable-operation refusals."""
    if host is not None:
        return {
            "status": "UNKNOWN",
            "refusal": "EXECUTION_UNAVAILABLE",
            "detail": "Direct host injection is unavailable; configure the shared solver port.",
        }
    return solve({**case, "challenge": "c014"})
