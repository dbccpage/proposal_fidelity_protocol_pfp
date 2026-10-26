"""Domain protocol and registry for cohomology challenge solvers.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class CohomologySolverPort(Protocol):
    """Protocol for solving cohomology challenge cases (C011-C020) via native Rust crates."""

    def solve(self, case: Mapping[str, Any]) -> dict[str, Any]:
        """Solve a cohomology case and return the certified result dictionary."""
        ...


_DEFAULT_SOLVER: CohomologySolverPort | None = None


def register_default_cohomology_solver(solver: CohomologySolverPort) -> None:
    """Register the active infrastructure solver adapter at composition root."""
    global _DEFAULT_SOLVER
    _DEFAULT_SOLVER = solver


def get_default_cohomology_solver() -> CohomologySolverPort:
    """Retrieve the registered solver, or raise an error if not injected."""
    if _DEFAULT_SOLVER is None:
        raise RuntimeError(
            "COHOMOLOGY_SOLVER_UNAVAILABLE: No CohomologySolverPort has been registered "
            "or injected by the composition root."
        )
    return _DEFAULT_SOLVER
