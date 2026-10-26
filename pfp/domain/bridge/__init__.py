"""
Symbol Game Bridge Package.

Exports:
- SymbolGamePacketCompiler, SymbolGameDialogueArguer, UnifiedNarrativeScriptEmitter
- ObstructionScore, SymbolGameStepResult
- ASTCochainExtractor, ASTDefect, ASTEvaluationReport
- UnifiedOETraceStore, UnifiedTraceRecord, PromptPerception
- PharmacySeeder, Antibody, ConstraintType, Operatorizability, RuntimeAction, Severity
- SBEAnalyzer, SBEDensityReport, SBE_DIMENSION
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .ast_cochain_extractor import ASTCochainExtractor, ASTDefect, ASTEvaluationReport
    from .pharmacy_seeder import Antibody, ConstraintType, Operatorizability, PharmacySeeder, PharmacyStatus, RuntimeAction, Severity
    from .sbe import SBE_DIMENSION, SBEAnalyzer, SBEDensityReport
    from .symbol_game_engine import ObstructionScore, SymbolGameDialogueArguer, SymbolGamePacketCompiler, SymbolGameStepResult, UnifiedNarrativeScriptEmitter
    from .unified_oe_trace import PromptPerception, UnifiedOETraceStore, UnifiedTraceRecord

__all__ = ['ASTCochainExtractor', 'ASTDefect', 'ASTEvaluationReport', 'Antibody', 'ConstraintType', 'Operatorizability', 'PharmacySeeder', 'PharmacyStatus', 'PromptPerception', 'RuntimeAction', 'SBE_DIMENSION', 'SBEAnalyzer', 'SBEDensityReport', 'Severity', 'ObstructionScore', 'SymbolGameDialogueArguer', 'SymbolGamePacketCompiler', 'SymbolGameStepResult', 'UnifiedNarrativeScriptEmitter', 'UnifiedOETraceStore', 'UnifiedTraceRecord']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ASTCochainExtractor': ('.ast_cochain_extractor', 'ASTCochainExtractor'),
    'ASTDefect': ('.ast_cochain_extractor', 'ASTDefect'),
    'ASTEvaluationReport': ('.ast_cochain_extractor', 'ASTEvaluationReport'),
    'Antibody': ('.pharmacy_seeder', 'Antibody'),
    'ConstraintType': ('.pharmacy_seeder', 'ConstraintType'),
    'Operatorizability': ('.pharmacy_seeder', 'Operatorizability'),
    'PharmacySeeder': ('.pharmacy_seeder', 'PharmacySeeder'),
    'PharmacyStatus': ('.pharmacy_seeder', 'PharmacyStatus'),
    'RuntimeAction': ('.pharmacy_seeder', 'RuntimeAction'),
    'Severity': ('.pharmacy_seeder', 'Severity'),
    'SBE_DIMENSION': ('.sbe', 'SBE_DIMENSION'),
    'SBEAnalyzer': ('.sbe', 'SBEAnalyzer'),
    'SBEDensityReport': ('.sbe', 'SBEDensityReport'),
    'ObstructionScore': ('.symbol_game_engine', 'ObstructionScore'),
    'SymbolGameDialogueArguer': ('.symbol_game_engine', 'SymbolGameDialogueArguer'),
    'SymbolGamePacketCompiler': ('.symbol_game_engine', 'SymbolGamePacketCompiler'),
    'SymbolGameStepResult': ('.symbol_game_engine', 'SymbolGameStepResult'),
    'UnifiedNarrativeScriptEmitter': ('.symbol_game_engine', 'UnifiedNarrativeScriptEmitter'),
    'PromptPerception': ('.unified_oe_trace', 'PromptPerception'),
    'UnifiedOETraceStore': ('.unified_oe_trace', 'UnifiedOETraceStore'),
    'UnifiedTraceRecord': ('.unified_oe_trace', 'UnifiedTraceRecord'),
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
