"""Discrete Deformation Calculus (DDC) Domain Models.

Implements the 8-letter operational trace alphabet, candidate runtime laws,
step receipts, and homotopy deformation transitions.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .alphabet import DDCRune
    from .runtime_laws import DDCRuntimeLawValidator, DDCValidationError
    from .trace import Commutator, DDCTrace, StepReceipt, TransitionStep

__all__ = ['DDCRune', 'TransitionStep', 'StepReceipt', 'DDCTrace', 'Commutator', 'DDCRuntimeLawValidator', 'DDCValidationError']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'DDCRune': ('.alphabet', 'DDCRune'),
    'DDCRuntimeLawValidator': ('.runtime_laws', 'DDCRuntimeLawValidator'),
    'DDCValidationError': ('.runtime_laws', 'DDCValidationError'),
    'Commutator': ('.trace', 'Commutator'),
    'DDCTrace': ('.trace', 'DDCTrace'),
    'StepReceipt': ('.trace', 'StepReceipt'),
    'TransitionStep': ('.trace', 'TransitionStep'),
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
