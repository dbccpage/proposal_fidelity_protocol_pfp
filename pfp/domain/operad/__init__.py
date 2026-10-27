"""Polarized Coloured Operad domain package.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pfp.domain.operad.errors import ArityMismatchError, IllTypedCompositionError, OperadError, OperadRoleViolationError, ProhibitedEvaluationError, ProhibitedRepairError, SliceViolationError
    from pfp.domain.operad.graft import GraftSite, PlanarGraft
    from pfp.domain.operad.morphisms import CandidatePatch, ConstructiveMorphism, Finding, InterrogativeMorphism, RepairMorphism
    from pfp.domain.operad.operad import PolarizedOperadTriad
    from pfp.domain.operad.polarity import Polarity
    from pfp.domain.operad.prompt import AnnihilatorDecoy, ColouredOperadPrompt, CongruenceIdeal, LeafTextSpan, NullTree, OperadTreeNode, PromptColour, PromptOperator

__all__ = ['AnnihilatorDecoy', 'ArityMismatchError', 'CandidatePatch', 'ColouredOperadPrompt', 'CongruenceIdeal', 'ConstructiveMorphism', 'Finding', 'GraftSite', 'IllTypedCompositionError', 'InterrogativeMorphism', 'LeafTextSpan', 'NullTree', 'OperadError', 'OperadRoleViolationError', 'OperadTreeNode', 'PlanarGraft', 'Polarity', 'PolarizedOperadTriad', 'ProhibitedEvaluationError', 'ProhibitedRepairError', 'PromptColour', 'PromptOperator', 'RepairMorphism', 'SliceViolationError']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ArityMismatchError': ('pfp.domain.operad.errors', 'ArityMismatchError'),
    'IllTypedCompositionError': ('pfp.domain.operad.errors', 'IllTypedCompositionError'),
    'OperadError': ('pfp.domain.operad.errors', 'OperadError'),
    'OperadRoleViolationError': ('pfp.domain.operad.errors', 'OperadRoleViolationError'),
    'ProhibitedEvaluationError': ('pfp.domain.operad.errors', 'ProhibitedEvaluationError'),
    'ProhibitedRepairError': ('pfp.domain.operad.errors', 'ProhibitedRepairError'),
    'SliceViolationError': ('pfp.domain.operad.errors', 'SliceViolationError'),
    'GraftSite': ('pfp.domain.operad.graft', 'GraftSite'),
    'PlanarGraft': ('pfp.domain.operad.graft', 'PlanarGraft'),
    'CandidatePatch': ('pfp.domain.operad.morphisms', 'CandidatePatch'),
    'ConstructiveMorphism': ('pfp.domain.operad.morphisms', 'ConstructiveMorphism'),
    'Finding': ('pfp.domain.operad.morphisms', 'Finding'),
    'InterrogativeMorphism': ('pfp.domain.operad.morphisms', 'InterrogativeMorphism'),
    'RepairMorphism': ('pfp.domain.operad.morphisms', 'RepairMorphism'),
    'PolarizedOperadTriad': ('pfp.domain.operad.operad', 'PolarizedOperadTriad'),
    'Polarity': ('pfp.domain.operad.polarity', 'Polarity'),
    'AnnihilatorDecoy': ('pfp.domain.operad.prompt', 'AnnihilatorDecoy'),
    'ColouredOperadPrompt': ('pfp.domain.operad.prompt', 'ColouredOperadPrompt'),
    'CongruenceIdeal': ('pfp.domain.operad.prompt', 'CongruenceIdeal'),
    'LeafTextSpan': ('pfp.domain.operad.prompt', 'LeafTextSpan'),
    'NullTree': ('pfp.domain.operad.prompt', 'NullTree'),
    'OperadTreeNode': ('pfp.domain.operad.prompt', 'OperadTreeNode'),
    'PromptColour': ('pfp.domain.operad.prompt', 'PromptColour'),
    'PromptOperator': ('pfp.domain.operad.prompt', 'PromptOperator'),
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
