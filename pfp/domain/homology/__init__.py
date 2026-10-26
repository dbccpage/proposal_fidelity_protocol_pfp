"""Cellular Homology & Cycle Balance Bounded Context.

AuthorityEffect: None.
Governing standard: Exact Algebraic Topology, Nilpotency Fences, and Cycle Balancing.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .carrier import Carrier, Edge, ProtoSupport, StaticCellBounds
    from .cochain import BoundaryMatrix, Cochain, DualCertificate, IntegerChain, IntegerMatrix, SmithNormalFormResult
    from .cycle_balance import CycleBalanceCandidate, CycleBalanceProblem, CycleBalanceQuartet, CycleBalanceReceipt, CycleBalanceVerifier
    from .ddc import DDCStep, DDCTape, DifferencePrimitive

__all__ = ['BoundaryMatrix', 'Carrier', 'Cochain', 'CycleBalanceCandidate', 'CycleBalanceProblem', 'CycleBalanceQuartet', 'CycleBalanceReceipt', 'CycleBalanceVerifier', 'DDCStep', 'DDCTape', 'DifferencePrimitive', 'DualCertificate', 'Edge', 'IntegerChain', 'IntegerMatrix', 'ProtoSupport', 'SmithNormalFormResult', 'StaticCellBounds']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'Carrier': ('.carrier', 'Carrier'),
    'Edge': ('.carrier', 'Edge'),
    'ProtoSupport': ('.carrier', 'ProtoSupport'),
    'StaticCellBounds': ('.carrier', 'StaticCellBounds'),
    'BoundaryMatrix': ('.cochain', 'BoundaryMatrix'),
    'Cochain': ('.cochain', 'Cochain'),
    'DualCertificate': ('.cochain', 'DualCertificate'),
    'IntegerChain': ('.cochain', 'IntegerChain'),
    'IntegerMatrix': ('.cochain', 'IntegerMatrix'),
    'SmithNormalFormResult': ('.cochain', 'SmithNormalFormResult'),
    'CycleBalanceCandidate': ('.cycle_balance', 'CycleBalanceCandidate'),
    'CycleBalanceProblem': ('.cycle_balance', 'CycleBalanceProblem'),
    'CycleBalanceQuartet': ('.cycle_balance', 'CycleBalanceQuartet'),
    'CycleBalanceReceipt': ('.cycle_balance', 'CycleBalanceReceipt'),
    'CycleBalanceVerifier': ('.cycle_balance', 'CycleBalanceVerifier'),
    'DDCStep': ('.ddc', 'DDCStep'),
    'DDCTape': ('.ddc', 'DDCTape'),
    'DifferencePrimitive': ('.ddc', 'DifferencePrimitive'),
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
