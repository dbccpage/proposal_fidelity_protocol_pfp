"""Typed Prompt Representations Package for Proposal Fidelity Protocol (PFP).

Provides sovereign, typed Pydantic models and YAML specifications for eight
prompt wire representations:
1. Raw (plain unpartitioned source text)
2. Structured (canonical JSON segment partition)
3. Relational (SQLite DDL & prompt_spans rows)
4. Symbolic (MSS-N boundary wire with dialect legend and JSON codebook)
5. Operadic (3-Layer compact operad: Environment, TreeSkeleton, SpanTable)
6. E-Graph (Equational saturation normal form with e-classes)
7. Diagram (Monoidal category string diagram planar wire-and-box syntax)
8. Cochain (Simplicial complex & discrete exterior calculus boundary representation)

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .cochain_prompt_representation import CochainPromptRepresentation, CochainSpanBinding
    from .common import ROLE_TO_SYMBOLIC, SYMBOLIC_TO_ROLE, BaseRepresentationRecord, Digest, RepresentationKind, Role, canonical_json_bytes, canonical_json_str, sha256_digest
    from .diagram_prompt_representation import DiagramBox, DiagramPromptRepresentation, DiagramSpanBinding, DiagramWire
    from .egraph_prompt_representation import EgraphPromptRepresentation, EgraphSpanBinding, NormalFormLevel
    from .operadic_prompt_representation import OperadEnvironment, OperadicPromptRepresentation, OperadSpanBinding, OperadSpanTable, OperadTreeSkeleton
    from .raw_prompt_representation import RawPromptRepresentation
    from .relational_prompt_representation import RelationalPromptRepresentation, RelationalSpanRow, SqlitePromptRepresentation
    from .structured_prompt_representation import StructuredPayload, StructuredPromptRepresentation, StructuredSegmentBinding
    from .symbolic_prompt_representation import DEFAULT_SYMBOLIC_LEGEND, SymbolicPromptRepresentation

__all__ = ['BaseRepresentationRecord', 'Digest', 'Role', 'RepresentationKind', 'ROLE_TO_SYMBOLIC', 'SYMBOLIC_TO_ROLE', 'sha256_digest', 'canonical_json_bytes', 'canonical_json_str', 'RawPromptRepresentation', 'StructuredPromptRepresentation', 'StructuredPayload', 'StructuredSegmentBinding', 'RelationalPromptRepresentation', 'RelationalSpanRow', 'SqlitePromptRepresentation', 'SymbolicPromptRepresentation', 'DEFAULT_SYMBOLIC_LEGEND', 'OperadicPromptRepresentation', 'OperadEnvironment', 'OperadTreeSkeleton', 'OperadSpanTable', 'OperadSpanBinding', 'EgraphPromptRepresentation', 'EgraphSpanBinding', 'NormalFormLevel', 'DiagramPromptRepresentation', 'DiagramBox', 'DiagramWire', 'DiagramSpanBinding', 'CochainPromptRepresentation', 'CochainSpanBinding']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CochainPromptRepresentation': ('.cochain_prompt_representation', 'CochainPromptRepresentation'),
    'CochainSpanBinding': ('.cochain_prompt_representation', 'CochainSpanBinding'),
    'ROLE_TO_SYMBOLIC': ('.common', 'ROLE_TO_SYMBOLIC'),
    'SYMBOLIC_TO_ROLE': ('.common', 'SYMBOLIC_TO_ROLE'),
    'BaseRepresentationRecord': ('.common', 'BaseRepresentationRecord'),
    'Digest': ('.common', 'Digest'),
    'RepresentationKind': ('.common', 'RepresentationKind'),
    'Role': ('.common', 'Role'),
    'canonical_json_bytes': ('.common', 'canonical_json_bytes'),
    'canonical_json_str': ('.common', 'canonical_json_str'),
    'sha256_digest': ('.common', 'sha256_digest'),
    'DiagramBox': ('.diagram_prompt_representation', 'DiagramBox'),
    'DiagramPromptRepresentation': ('.diagram_prompt_representation', 'DiagramPromptRepresentation'),
    'DiagramSpanBinding': ('.diagram_prompt_representation', 'DiagramSpanBinding'),
    'DiagramWire': ('.diagram_prompt_representation', 'DiagramWire'),
    'EgraphPromptRepresentation': ('.egraph_prompt_representation', 'EgraphPromptRepresentation'),
    'EgraphSpanBinding': ('.egraph_prompt_representation', 'EgraphSpanBinding'),
    'NormalFormLevel': ('.egraph_prompt_representation', 'NormalFormLevel'),
    'OperadEnvironment': ('.operadic_prompt_representation', 'OperadEnvironment'),
    'OperadicPromptRepresentation': ('.operadic_prompt_representation', 'OperadicPromptRepresentation'),
    'OperadSpanBinding': ('.operadic_prompt_representation', 'OperadSpanBinding'),
    'OperadSpanTable': ('.operadic_prompt_representation', 'OperadSpanTable'),
    'OperadTreeSkeleton': ('.operadic_prompt_representation', 'OperadTreeSkeleton'),
    'RawPromptRepresentation': ('.raw_prompt_representation', 'RawPromptRepresentation'),
    'RelationalPromptRepresentation': ('.relational_prompt_representation', 'RelationalPromptRepresentation'),
    'RelationalSpanRow': ('.relational_prompt_representation', 'RelationalSpanRow'),
    'SqlitePromptRepresentation': ('.relational_prompt_representation', 'SqlitePromptRepresentation'),
    'StructuredPayload': ('.structured_prompt_representation', 'StructuredPayload'),
    'StructuredPromptRepresentation': ('.structured_prompt_representation', 'StructuredPromptRepresentation'),
    'StructuredSegmentBinding': ('.structured_prompt_representation', 'StructuredSegmentBinding'),
    'DEFAULT_SYMBOLIC_LEGEND': ('.symbolic_prompt_representation', 'DEFAULT_SYMBOLIC_LEGEND'),
    'SymbolicPromptRepresentation': ('.symbolic_prompt_representation', 'SymbolicPromptRepresentation'),
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
