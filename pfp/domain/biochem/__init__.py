"""Biochemical Swarm Gates domain package.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pfp.domain.biochem.allostery import AllostericConsensusGate, AllostericDecision, HillParameters
    from pfp.domain.biochem.errors import BiochemError, DissociationError, ZeroFloatViolationError
    from pfp.domain.biochem.proofreading import DissociationReceipt, HopfieldNinioProofreader, KineticProofreadingState

__all__ = ['AllostericConsensusGate', 'AllostericDecision', 'BiochemError', 'DissociationError', 'HillParameters', 'HopfieldNinioProofreader', 'KineticProofreadingState', 'DissociationReceipt', 'ZeroFloatViolationError']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AllostericConsensusGate': ('pfp.domain.biochem.allostery', 'AllostericConsensusGate'),
    'AllostericDecision': ('pfp.domain.biochem.allostery', 'AllostericDecision'),
    'HillParameters': ('pfp.domain.biochem.allostery', 'HillParameters'),
    'BiochemError': ('pfp.domain.biochem.errors', 'BiochemError'),
    'DissociationError': ('pfp.domain.biochem.errors', 'DissociationError'),
    'ZeroFloatViolationError': ('pfp.domain.biochem.errors', 'ZeroFloatViolationError'),
    'DissociationReceipt': ('pfp.domain.biochem.proofreading', 'DissociationReceipt'),
    'HopfieldNinioProofreader': ('pfp.domain.biochem.proofreading', 'HopfieldNinioProofreader'),
    'KineticProofreadingState': ('pfp.domain.biochem.proofreading', 'KineticProofreadingState'),
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
