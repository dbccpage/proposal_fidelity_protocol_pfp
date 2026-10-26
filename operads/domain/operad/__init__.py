"""
Domain Layer - Coloured Operads & Morphisms
===========================================

Canonical domain models for multi-coloured symmetric operads,
colour signatures, operations, planar tree compositions,
and agent capability slices.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .colours import ADMITTED_FINITE_COLOURS, Colour, ColourSignature
    from .errors import ArityMismatchError, DomainError, Err, IllTypedCompositionError, InvalidColourError, MissingUnitError, Ok, OperadAssociativityError, OperadDomainError, Result, SkillSignatureRefusal, SliceViolationError
    from .evidence import EvidenceObservation, EvidenceReceipt, EvidenceType
    from .operad import AgentSlice, ColouredOperad
    from .operation import OperationId, OperationSignature
    from .planar import PlanarTree, TreeCompositionWitness
    from .treg import OperadTregReceipt, OperadTregSupervisor

__all__ = ['ADMITTED_FINITE_COLOURS', 'Colour', 'ColourSignature', 'OperationId', 'OperationSignature', 'ColouredOperad', 'AgentSlice', 'PlanarTree', 'TreeCompositionWitness', 'EvidenceReceipt', 'EvidenceObservation', 'EvidenceType', 'OperadTregReceipt', 'OperadTregSupervisor', 'DomainError', 'OperadDomainError', 'InvalidColourError', 'ArityMismatchError', 'IllTypedCompositionError', 'OperadAssociativityError', 'SliceViolationError', 'MissingUnitError', 'SkillSignatureRefusal', 'Result', 'Ok', 'Err']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ADMITTED_FINITE_COLOURS': ('.colours', 'ADMITTED_FINITE_COLOURS'),
    'Colour': ('.colours', 'Colour'),
    'ColourSignature': ('.colours', 'ColourSignature'),
    'ArityMismatchError': ('.errors', 'ArityMismatchError'),
    'DomainError': ('.errors', 'DomainError'),
    'Err': ('.errors', 'Err'),
    'IllTypedCompositionError': ('.errors', 'IllTypedCompositionError'),
    'InvalidColourError': ('.errors', 'InvalidColourError'),
    'MissingUnitError': ('.errors', 'MissingUnitError'),
    'Ok': ('.errors', 'Ok'),
    'OperadAssociativityError': ('.errors', 'OperadAssociativityError'),
    'OperadDomainError': ('.errors', 'OperadDomainError'),
    'Result': ('.errors', 'Result'),
    'SkillSignatureRefusal': ('.errors', 'SkillSignatureRefusal'),
    'SliceViolationError': ('.errors', 'SliceViolationError'),
    'EvidenceObservation': ('.evidence', 'EvidenceObservation'),
    'EvidenceReceipt': ('.evidence', 'EvidenceReceipt'),
    'EvidenceType': ('.evidence', 'EvidenceType'),
    'AgentSlice': ('.operad', 'AgentSlice'),
    'ColouredOperad': ('.operad', 'ColouredOperad'),
    'OperationId': ('.operation', 'OperationId'),
    'OperationSignature': ('.operation', 'OperationSignature'),
    'PlanarTree': ('.planar', 'PlanarTree'),
    'TreeCompositionWitness': ('.planar', 'TreeCompositionWitness'),
    'OperadTregReceipt': ('.treg', 'OperadTregReceipt'),
    'OperadTregSupervisor': ('.treg', 'OperadTregSupervisor'),
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
