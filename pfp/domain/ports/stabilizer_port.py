"""Domain port for quantum stabilizer solver and checker.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class StabilizerPort(Protocol):
    """Protocol for finite quantum stabilizer solver and total certificate checker."""

    @property
    def native_outcomes(self) -> tuple[Mapping[str, Any], ...]:
        """Complete native runtime envelopes retained before payload extraction."""
        ...

    def solve(self, case: Mapping[str, Any]) -> dict[str, Any]:
        """Solve a finite quantum Hamiltonian challenge case."""
        ...

    def check(self, case: Mapping[str, Any], result: Any) -> dict[str, Any]:
        """Verify solver solution against case in total algebraic checker."""
        ...
