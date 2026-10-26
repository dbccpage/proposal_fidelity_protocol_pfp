"""Polarized Coloured Operad domain package.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_pfp.domain.operad.errors import ArityMismatchError, IllTypedCompositionError, OperadError, OperadRoleViolationError, ProhibitedEvaluationError, ProhibitedRepairError, SliceViolationError
    from omega_engine_pfp.domain.operad.graft import GraftSite, PlanarGraft
    from omega_engine_pfp.domain.operad.morphisms import CandidatePatch, ConstructiveMorphism, Finding, InterrogativeMorphism, RepairMorphism
    from omega_engine_pfp.domain.operad.operad import PolarizedOperadTriad
    from omega_engine_pfp.domain.operad.polarity import Polarity
    from omega_engine_pfp.domain.operad.prompt import AnnihilatorDecoy, ColouredOperadPrompt, CongruenceIdeal, LeafTextSpan, NullTree, OperadTreeNode, PromptColour, PromptOperator

__all__ = ['AnnihilatorDecoy', 'ArityMismatchError', 'CandidatePatch', 'ColouredOperadPrompt', 'CongruenceIdeal', 'ConstructiveMorphism', 'Finding', 'GraftSite', 'IllTypedCompositionError', 'InterrogativeMorphism', 'LeafTextSpan', 'NullTree', 'OperadError', 'OperadRoleViolationError', 'OperadTreeNode', 'PlanarGraft', 'Polarity', 'PolarizedOperadTriad', 'ProhibitedEvaluationError', 'ProhibitedRepairError', 'PromptColour', 'PromptOperator', 'RepairMorphism', 'SliceViolationError']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ArityMismatchError': ('omega_engine_pfp.domain.operad.errors', 'ArityMismatchError'),
    'IllTypedCompositionError': ('omega_engine_pfp.domain.operad.errors', 'IllTypedCompositionError'),
    'OperadError': ('omega_engine_pfp.domain.operad.errors', 'OperadError'),
    'OperadRoleViolationError': ('omega_engine_pfp.domain.operad.errors', 'OperadRoleViolationError'),
    'ProhibitedEvaluationError': ('omega_engine_pfp.domain.operad.errors', 'ProhibitedEvaluationError'),
    'ProhibitedRepairError': ('omega_engine_pfp.domain.operad.errors', 'ProhibitedRepairError'),
    'SliceViolationError': ('omega_engine_pfp.domain.operad.errors', 'SliceViolationError'),
    'GraftSite': ('omega_engine_pfp.domain.operad.graft', 'GraftSite'),
    'PlanarGraft': ('omega_engine_pfp.domain.operad.graft', 'PlanarGraft'),
    'CandidatePatch': ('omega_engine_pfp.domain.operad.morphisms', 'CandidatePatch'),
    'ConstructiveMorphism': ('omega_engine_pfp.domain.operad.morphisms', 'ConstructiveMorphism'),
    'Finding': ('omega_engine_pfp.domain.operad.morphisms', 'Finding'),
    'InterrogativeMorphism': ('omega_engine_pfp.domain.operad.morphisms', 'InterrogativeMorphism'),
    'RepairMorphism': ('omega_engine_pfp.domain.operad.morphisms', 'RepairMorphism'),
    'PolarizedOperadTriad': ('omega_engine_pfp.domain.operad.operad', 'PolarizedOperadTriad'),
    'Polarity': ('omega_engine_pfp.domain.operad.polarity', 'Polarity'),
    'AnnihilatorDecoy': ('omega_engine_pfp.domain.operad.prompt', 'AnnihilatorDecoy'),
    'ColouredOperadPrompt': ('omega_engine_pfp.domain.operad.prompt', 'ColouredOperadPrompt'),
    'CongruenceIdeal': ('omega_engine_pfp.domain.operad.prompt', 'CongruenceIdeal'),
    'LeafTextSpan': ('omega_engine_pfp.domain.operad.prompt', 'LeafTextSpan'),
    'NullTree': ('omega_engine_pfp.domain.operad.prompt', 'NullTree'),
    'OperadTreeNode': ('omega_engine_pfp.domain.operad.prompt', 'OperadTreeNode'),
    'PromptColour': ('omega_engine_pfp.domain.operad.prompt', 'PromptColour'),
    'PromptOperator': ('omega_engine_pfp.domain.operad.prompt', 'PromptOperator'),
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
