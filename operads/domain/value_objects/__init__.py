"""Value objects for OEWAS V3 domain."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .authority import AUTHORITY_RANK, AuthorityEffect
    from .byte_span import SourceByteSpan
    from .content_digest import ContentDigest
    from .identifier import CausationId, ColourId, CorrelationId, DocumentId, EstateRef, IdempotencyKey, OperandId, OperationId, SchemaRef, SkillId, WorkflowId
    from .lifecycle_facets import AdmissionFacet, DeclarationFacet, ExecutorBindingFacet, SchemaBindingFacet, SkillLifecycleV3, ValidationFacet
    from .operands import ArtifactOperandRef, InstructionOperand, ResidualPackageSpan

__all__ = ['AUTHORITY_RANK', 'AdmissionFacet', 'ArtifactOperandRef', 'AuthorityEffect', 'CausationId', 'ColourId', 'ContentDigest', 'CorrelationId', 'DeclarationFacet', 'DocumentId', 'EstateRef', 'ExecutorBindingFacet', 'IdempotencyKey', 'InstructionOperand', 'OperandId', 'OperationId', 'ResidualPackageSpan', 'SchemaBindingFacet', 'SchemaRef', 'SkillId', 'SkillLifecycleV3', 'SourceByteSpan', 'ValidationFacet', 'WorkflowId']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AUTHORITY_RANK': ('.authority', 'AUTHORITY_RANK'),
    'AuthorityEffect': ('.authority', 'AuthorityEffect'),
    'SourceByteSpan': ('.byte_span', 'SourceByteSpan'),
    'ContentDigest': ('.content_digest', 'ContentDigest'),
    'CausationId': ('.identifier', 'CausationId'),
    'ColourId': ('.identifier', 'ColourId'),
    'CorrelationId': ('.identifier', 'CorrelationId'),
    'DocumentId': ('.identifier', 'DocumentId'),
    'EstateRef': ('.identifier', 'EstateRef'),
    'IdempotencyKey': ('.identifier', 'IdempotencyKey'),
    'OperandId': ('.identifier', 'OperandId'),
    'OperationId': ('.identifier', 'OperationId'),
    'SchemaRef': ('.identifier', 'SchemaRef'),
    'SkillId': ('.identifier', 'SkillId'),
    'WorkflowId': ('.identifier', 'WorkflowId'),
    'AdmissionFacet': ('.lifecycle_facets', 'AdmissionFacet'),
    'DeclarationFacet': ('.lifecycle_facets', 'DeclarationFacet'),
    'ExecutorBindingFacet': ('.lifecycle_facets', 'ExecutorBindingFacet'),
    'SchemaBindingFacet': ('.lifecycle_facets', 'SchemaBindingFacet'),
    'SkillLifecycleV3': ('.lifecycle_facets', 'SkillLifecycleV3'),
    'ValidationFacet': ('.lifecycle_facets', 'ValidationFacet'),
    'ArtifactOperandRef': ('.operands', 'ArtifactOperandRef'),
    'InstructionOperand': ('.operands', 'InstructionOperand'),
    'ResidualPackageSpan': ('.operands', 'ResidualPackageSpan'),
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
