"""Operad Domain Layer.

Canonical domain-layer implementations for new code. Historical root registry
and adapter APIs remain explicit compatibility surfaces until their contracts
are proved API-equivalent.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .antibodies import AntiMorphism, make_ast_pattern_antibody, pullback_antibody, scan_source_for_pitfalls
    from .colours import ADMITTED_FINITE_COLOURS, Colour, ColourSignature
    from .errors import ArityMismatchError, DomainError, Err, Failure, IllTypedCompositionError, InvalidColourError, InvariantViolationError, MissingUnitError, Ok, Result, SliceViolationError, Success
    from .evidence import CommandRecord, ConcreteWitness, DiagnosticObservation, EvidenceReceipt, HallucinationWitness, PathObstructionWitness, Residual, Witness, EMPTY
    from .hott import Homotopy2Cell, Path, identity_path, refl, transport, transport_along_path
    from omega_engine_operads.domain.operad.operad import AgentSlice, ColouredOperad
    from omega_engine_operads.domain.operad.operation import OperationId, OperationSignature
    from .planar import ArgumentCountError, ArityMismatch, Color, ColorMismatch, ColoredOp, OperadError, Term, formal_compose, identity, nullary, receipt_to_residual
    from .ports import FileLockPort, OperadRepositoryPort, null_file_lock
    from .span_operands import DocumentSpanPartition, SpanMulticategoryMorphism, SpanOperand, partition_markdown_document

__all__ = ['ADMITTED_FINITE_COLOURS', 'AgentSlice', 'AntiMorphism', 'ArgumentCountError', 'ArityMismatch', 'ArityMismatchError', 'Color', 'ColorMismatch', 'ColoredOp', 'Colour', 'ColourSignature', 'ColouredOperad', 'CommandRecord', 'ConcreteWitness', 'DiagnosticObservation', 'DocumentSpanPartition', 'DomainError', 'EMPTY', 'Err', 'EvidenceReceipt', 'Failure', 'FileLockPort', 'HallucinationWitness', 'Homotopy2Cell', 'IllTypedCompositionError', 'InvalidColourError', 'InvariantViolationError', 'MissingUnitError', 'Ok', 'OperadError', 'OperadRepositoryPort', 'OperationId', 'OperationSignature', 'Path', 'PathObstructionWitness', 'Residual', 'Result', 'SliceViolationError', 'SpanMulticategoryMorphism', 'SpanOperand', 'Success', 'Term', 'Witness', 'formal_compose', 'identity', 'identity_path', 'make_ast_pattern_antibody', 'null_file_lock', 'nullary', 'partition_markdown_document', 'pullback_antibody', 'receipt_to_residual', 'refl', 'scan_source_for_pitfalls', 'transport', 'transport_along_path']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AntiMorphism': ('.antibodies', 'AntiMorphism'),
    'make_ast_pattern_antibody': ('.antibodies', 'make_ast_pattern_antibody'),
    'pullback_antibody': ('.antibodies', 'pullback_antibody'),
    'scan_source_for_pitfalls': ('.antibodies', 'scan_source_for_pitfalls'),
    'ADMITTED_FINITE_COLOURS': ('.colours', 'ADMITTED_FINITE_COLOURS'),
    'Colour': ('.colours', 'Colour'),
    'ColourSignature': ('.colours', 'ColourSignature'),
    'ArityMismatchError': ('.errors', 'ArityMismatchError'),
    'DomainError': ('.errors', 'DomainError'),
    'Err': ('.errors', 'Err'),
    'Failure': ('.errors', 'Failure'),
    'IllTypedCompositionError': ('.errors', 'IllTypedCompositionError'),
    'InvalidColourError': ('.errors', 'InvalidColourError'),
    'InvariantViolationError': ('.errors', 'InvariantViolationError'),
    'MissingUnitError': ('.errors', 'MissingUnitError'),
    'Ok': ('.errors', 'Ok'),
    'Result': ('.errors', 'Result'),
    'SliceViolationError': ('.errors', 'SliceViolationError'),
    'Success': ('.errors', 'Success'),
    'CommandRecord': ('.evidence', 'CommandRecord'),
    'ConcreteWitness': ('.evidence', 'ConcreteWitness'),
    'DiagnosticObservation': ('.evidence', 'DiagnosticObservation'),
    'EvidenceReceipt': ('.evidence', 'EvidenceReceipt'),
    'HallucinationWitness': ('.evidence', 'HallucinationWitness'),
    'PathObstructionWitness': ('.evidence', 'PathObstructionWitness'),
    'Residual': ('.evidence', 'Residual'),
    'Witness': ('.evidence', 'Witness'),
    'EMPTY': ('.evidence', 'EMPTY'),
    'Homotopy2Cell': ('.hott', 'Homotopy2Cell'),
    'Path': ('.hott', 'Path'),
    'identity_path': ('.hott', 'identity_path'),
    'refl': ('.hott', 'refl'),
    'transport': ('.hott', 'transport'),
    'transport_along_path': ('.hott', 'transport_along_path'),
    'AgentSlice': ('omega_engine_operads.domain.operad.operad', 'AgentSlice'),
    'ColouredOperad': ('omega_engine_operads.domain.operad.operad', 'ColouredOperad'),
    'OperationId': ('omega_engine_operads.domain.operad.operation', 'OperationId'),
    'OperationSignature': ('omega_engine_operads.domain.operad.operation', 'OperationSignature'),
    'ArgumentCountError': ('.planar', 'ArgumentCountError'),
    'ArityMismatch': ('.planar', 'ArityMismatch'),
    'Color': ('.planar', 'Color'),
    'ColorMismatch': ('.planar', 'ColorMismatch'),
    'ColoredOp': ('.planar', 'ColoredOp'),
    'OperadError': ('.planar', 'OperadError'),
    'Term': ('.planar', 'Term'),
    'formal_compose': ('.planar', 'formal_compose'),
    'identity': ('.planar', 'identity'),
    'nullary': ('.planar', 'nullary'),
    'receipt_to_residual': ('.planar', 'receipt_to_residual'),
    'FileLockPort': ('.ports', 'FileLockPort'),
    'OperadRepositoryPort': ('.ports', 'OperadRepositoryPort'),
    'null_file_lock': ('.ports', 'null_file_lock'),
    'DocumentSpanPartition': ('.span_operands', 'DocumentSpanPartition'),
    'SpanMulticategoryMorphism': ('.span_operands', 'SpanMulticategoryMorphism'),
    'SpanOperand': ('.span_operands', 'SpanOperand'),
    'partition_markdown_document': ('.span_operands', 'partition_markdown_document'),
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
