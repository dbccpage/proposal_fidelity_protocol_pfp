"""Constrained decoding, 2-polygraph confluence, antimorphic reversal, and information cohomology.

Pure domain package with zero outward dependencies.
AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .antimorphism import AntimorphismTransitionModel, EdgeInvolution, ProtectedDistinction, ReversalMap
    from .cohomology import EntropyCocycle, EpistemicQuarantineLedger, InformationCohomologyBarcode, PersistenceInterval, QuarantinedShadowPacket
    from .errors import DecodingError, DecodingRefusalCode, InvolutionIdentityError, ProtectedDistinctionCollapseError, RefusedZeroRetainedMassError, ZeroFloatViolationError
    from .polygraph import Confluence2Cell, CriticalPair, RewriteStep, TarskiPolygraph
    from .token_frontier import FrontierCandidate, TokenFrontier
    from .vocabulary import RetainedProbabilityMass, WireVocabulary

__all__ = ['AntimorphismTransitionModel', 'Confluence2Cell', 'CriticalPair', 'DecodingError', 'DecodingRefusalCode', 'EdgeInvolution', 'EntropyCocycle', 'EpistemicQuarantineLedger', 'FrontierCandidate', 'InformationCohomologyBarcode', 'InvolutionIdentityError', 'PersistenceInterval', 'ProtectedDistinction', 'ProtectedDistinctionCollapseError', 'QuarantinedShadowPacket', 'RefusedZeroRetainedMassError', 'RetainedProbabilityMass', 'ReversalMap', 'RewriteStep', 'TarskiPolygraph', 'TokenFrontier', 'WireVocabulary', 'ZeroFloatViolationError']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AntimorphismTransitionModel': ('.antimorphism', 'AntimorphismTransitionModel'),
    'EdgeInvolution': ('.antimorphism', 'EdgeInvolution'),
    'ProtectedDistinction': ('.antimorphism', 'ProtectedDistinction'),
    'ReversalMap': ('.antimorphism', 'ReversalMap'),
    'EntropyCocycle': ('.cohomology', 'EntropyCocycle'),
    'EpistemicQuarantineLedger': ('.cohomology', 'EpistemicQuarantineLedger'),
    'InformationCohomologyBarcode': ('.cohomology', 'InformationCohomologyBarcode'),
    'PersistenceInterval': ('.cohomology', 'PersistenceInterval'),
    'QuarantinedShadowPacket': ('.cohomology', 'QuarantinedShadowPacket'),
    'DecodingError': ('.errors', 'DecodingError'),
    'DecodingRefusalCode': ('.errors', 'DecodingRefusalCode'),
    'InvolutionIdentityError': ('.errors', 'InvolutionIdentityError'),
    'ProtectedDistinctionCollapseError': ('.errors', 'ProtectedDistinctionCollapseError'),
    'RefusedZeroRetainedMassError': ('.errors', 'RefusedZeroRetainedMassError'),
    'ZeroFloatViolationError': ('.errors', 'ZeroFloatViolationError'),
    'Confluence2Cell': ('.polygraph', 'Confluence2Cell'),
    'CriticalPair': ('.polygraph', 'CriticalPair'),
    'RewriteStep': ('.polygraph', 'RewriteStep'),
    'TarskiPolygraph': ('.polygraph', 'TarskiPolygraph'),
    'FrontierCandidate': ('.token_frontier', 'FrontierCandidate'),
    'TokenFrontier': ('.token_frontier', 'TokenFrontier'),
    'RetainedProbabilityMass': ('.vocabulary', 'RetainedProbabilityMass'),
    'WireVocabulary': ('.vocabulary', 'WireVocabulary'),
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
