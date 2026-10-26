"""Finite quantum stabilizer domain package.

Includes Pauli string algebra, the finite Hamiltonian parser, and the
unbound stabilizer port. The port refuses until a StabilizerPort is injected.
AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .hamiltonian import HamiltonianTerm, QuantumHamiltonian
    from .pauli import PauliString
    from .stabilizer_solver import solve

__all__ = ['HamiltonianTerm', 'PauliString', 'QuantumHamiltonian', 'solve']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'HamiltonianTerm': ('.hamiltonian', 'HamiltonianTerm'),
    'QuantumHamiltonian': ('.hamiltonian', 'QuantumHamiltonian'),
    'PauliString': ('.pauli', 'PauliString'),
    'solve': ('.stabilizer_solver', 'solve'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
