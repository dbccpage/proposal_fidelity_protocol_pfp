"""
Challenge C055 reference solver entry point.
"""

from typing import Any, Dict

from .hungarian import solve_assignment


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    return solve_assignment(case)
