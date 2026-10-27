"""
Challenge C054 reference solver entry point.
"""

from typing import Any, Dict

from .linear_solver import solve_linear_system


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    return solve_linear_system(case)
