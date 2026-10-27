"""Calculus of Obstruction, Descent, and Authority (CODA) Domain Models.

Implements the Nine-Layer Stack, exact dual witness certificates,
continuum enclosure bounds, Seven Halt Guards, and GTLA terminalization.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .dual_witness import DualWitnessCertificate, ExactDualWitnessValidator
    from .gtla_authority import GTLAResult, GTLATerminalOutcome
    from .halt_guards import HaltGuardResult, SevenHaltGuards
    from .layers import CODALayer

__all__ = ['CODALayer', 'DualWitnessCertificate', 'ExactDualWitnessValidator', 'SevenHaltGuards', 'HaltGuardResult', 'GTLATerminalOutcome', 'GTLAResult']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'DualWitnessCertificate': ('.dual_witness', 'DualWitnessCertificate'),
    'ExactDualWitnessValidator': ('.dual_witness', 'ExactDualWitnessValidator'),
    'GTLAResult': ('.gtla_authority', 'GTLAResult'),
    'GTLATerminalOutcome': ('.gtla_authority', 'GTLATerminalOutcome'),
    'HaltGuardResult': ('.halt_guards', 'HaltGuardResult'),
    'SevenHaltGuards': ('.halt_guards', 'SevenHaltGuards'),
    'CODALayer': ('.layers', 'CODALayer'),
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
