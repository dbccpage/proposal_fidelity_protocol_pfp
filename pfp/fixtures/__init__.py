"""Finite, deterministic fixtures for falsifying the lab hypothesis."""

from .finite_csp import (
    ExhaustiveCspSolver,
    FiniteConstraint,
    FiniteCspProjector,
    NamedVariableRetraction,
    NoOpClaimingSolver,
    build_demo_problem,
)

__all__ = [
    "ExhaustiveCspSolver",
    "FiniteConstraint",
    "FiniteCspProjector",
    "NamedVariableRetraction",
    "NoOpClaimingSolver",
    "build_demo_problem",
]
