"""Protocol for Lean 4 Formal Verification and Axiom Totality."""

from __future__ import annotations

from typing import Protocol, Set


class Lean4VerifierPort(Protocol):
    """Protocol for executing Lean 4 proof elaboration and axiom auditing."""

    def verify_module(self, module_path: str) -> bool:
        """Executes Lake env lean to verify a theorem module elaborates without error."""
        ...

    def audit_axioms(self, module_path: str, theorem_name: str) -> Set[str]:
        """Returns the set of axioms used by theorem_name (flagging non-standard axioms or sorry)."""
        ...

    def check_theorem_exists(self, module_path: str, theorem_name: str) -> bool:
        """Verifies that theorem_name is defined and verified in module_path."""
        ...
