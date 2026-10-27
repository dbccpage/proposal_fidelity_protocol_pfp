"""StructureBench relational contract evaluation over Adversary bout artifacts.

`EPIC-OE-OEWAS-007`, target module `operads/structurebench`.

`AuthorityEffect: None`.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .errors import StructureBenchError
    from .evaluator import ACT_HEADERS, BIJECTION_KEYS, BUNDLE_FILES, CONSTRAINT_IDS, GATE_INCIDENCE, VALID_TERMINAL_VERDICTS, ConstraintOutcome, ConstraintResult, GateIncidenceAuditReport, StructureBenchEvaluator, StructureBenchReport, audit_gate_incidence, build_gate_incidence_matrix, evaluate_bundle
    from .path_bundle_reader import PathBundleReader
    from .ports import BundleReader

__all__ = ['ACT_HEADERS', 'BIJECTION_KEYS', 'BUNDLE_FILES', 'BundleReader', 'CONSTRAINT_IDS', 'GATE_INCIDENCE', 'GateIncidenceAuditReport', 'PathBundleReader', 'VALID_TERMINAL_VERDICTS', 'ConstraintOutcome', 'ConstraintResult', 'StructureBenchError', 'StructureBenchEvaluator', 'StructureBenchReport', 'audit_gate_incidence', 'build_gate_incidence_matrix', 'evaluate_bundle']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'StructureBenchError': ('.errors', 'StructureBenchError'),
    'ACT_HEADERS': ('.evaluator', 'ACT_HEADERS'),
    'BIJECTION_KEYS': ('.evaluator', 'BIJECTION_KEYS'),
    'BUNDLE_FILES': ('.evaluator', 'BUNDLE_FILES'),
    'CONSTRAINT_IDS': ('.evaluator', 'CONSTRAINT_IDS'),
    'GATE_INCIDENCE': ('.evaluator', 'GATE_INCIDENCE'),
    'VALID_TERMINAL_VERDICTS': ('.evaluator', 'VALID_TERMINAL_VERDICTS'),
    'ConstraintOutcome': ('.evaluator', 'ConstraintOutcome'),
    'ConstraintResult': ('.evaluator', 'ConstraintResult'),
    'GateIncidenceAuditReport': ('.evaluator', 'GateIncidenceAuditReport'),
    'StructureBenchEvaluator': ('.evaluator', 'StructureBenchEvaluator'),
    'StructureBenchReport': ('.evaluator', 'StructureBenchReport'),
    'audit_gate_incidence': ('.evaluator', 'audit_gate_incidence'),
    'build_gate_incidence_matrix': ('.evaluator', 'build_gate_incidence_matrix'),
    'evaluate_bundle': ('.evaluator', 'evaluate_bundle'),
    'PathBundleReader': ('.path_bundle_reader', 'PathBundleReader'),
    'BundleReader': ('.ports', 'BundleReader'),
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
