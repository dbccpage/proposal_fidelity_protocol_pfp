"""PFP Prompt Rewriting and Boundary Containment Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .prompt_containment import ExpansionNode, MutationKind, PipelineStage
    from .rewrites import Binding, Boundary, ComparisonTrial, RewriteReceipt, RewriteRequest, Segment, TrialObservation, parse_boundary
    from .rewriting_types import BoundaryWire, ByteSpan, CompilationReceipt, RewritingBase, SpanPartition, SpanRole, SymbolBinding
    from .wires import AppTerm, AtomTerm, SyntaxProfile, TokenLegend, VoidTerm, WireCodec, WirePacket, WireTerm, WireTermKind

__all__ = ['AppTerm', 'AtomTerm', 'Binding', 'Boundary', 'BoundaryWire', 'ByteSpan', 'ComparisonTrial', 'CompilationReceipt', 'ExpansionNode', 'MutationKind', 'PipelineStage', 'RewriteReceipt', 'RewriteRequest', 'RewritingBase', 'Segment', 'SpanPartition', 'SpanRole', 'SymbolBinding', 'SyntaxProfile', 'TokenLegend', 'TrialObservation', 'VoidTerm', 'WireCodec', 'WirePacket', 'WireTerm', 'WireTermKind', 'parse_boundary']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ExpansionNode': ('.prompt_containment', 'ExpansionNode'),
    'MutationKind': ('.prompt_containment', 'MutationKind'),
    'PipelineStage': ('.prompt_containment', 'PipelineStage'),
    'Binding': ('.rewrites', 'Binding'),
    'Boundary': ('.rewrites', 'Boundary'),
    'ComparisonTrial': ('.rewrites', 'ComparisonTrial'),
    'RewriteReceipt': ('.rewrites', 'RewriteReceipt'),
    'RewriteRequest': ('.rewrites', 'RewriteRequest'),
    'Segment': ('.rewrites', 'Segment'),
    'TrialObservation': ('.rewrites', 'TrialObservation'),
    'parse_boundary': ('.rewrites', 'parse_boundary'),
    'BoundaryWire': ('.rewriting_types', 'BoundaryWire'),
    'ByteSpan': ('.rewriting_types', 'ByteSpan'),
    'CompilationReceipt': ('.rewriting_types', 'CompilationReceipt'),
    'RewritingBase': ('.rewriting_types', 'RewritingBase'),
    'SpanPartition': ('.rewriting_types', 'SpanPartition'),
    'SpanRole': ('.rewriting_types', 'SpanRole'),
    'SymbolBinding': ('.rewriting_types', 'SymbolBinding'),
    'AppTerm': ('.wires', 'AppTerm'),
    'AtomTerm': ('.wires', 'AtomTerm'),
    'SyntaxProfile': ('.wires', 'SyntaxProfile'),
    'TokenLegend': ('.wires', 'TokenLegend'),
    'VoidTerm': ('.wires', 'VoidTerm'),
    'WireCodec': ('.wires', 'WireCodec'),
    'WirePacket': ('.wires', 'WirePacket'),
    'WireTerm': ('.wires', 'WireTerm'),
    'WireTermKind': ('.wires', 'WireTermKind'),
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
