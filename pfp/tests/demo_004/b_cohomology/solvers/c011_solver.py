"""Compatibility entrypoint for C011; execution belongs to the registered port."""

from __future__ import annotations

from typing import Any, Mapping

from pfp.domain.cohomology.solver import solve


def solve_c011(case: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve the owning solver's result, including unavailable-operation refusals."""
    return solve({**case, "challenge": "c011"})
