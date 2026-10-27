from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .omc_dag_models import CodeCompliance, DualWitnessStatus, GateStatus, NaturalScienceGates, OMCMonographAuditRecord, OMCPRReviewRecord, OMCRecord, OMCRecordType, OMCSubsystemAuditRecord, OMCVerdict, parse_omc_dict, parse_omc_line, parse_omc_markdown
    from .paper_review_models import AccomplishmentItem, AccomplishmentKind, FailureObstructionItem, ObstructionKind, PaperReviewDigestRecord, RecordType, ReviewStatus, ReviewSummary, Severity
    from .ports import IntelligenceCollectionPort, IntelligenceCollectionReceipt, IntelligenceDigestionFileSystemPort, IntelligenceLifecyclePort

__all__ = ['AccomplishmentItem', 'AccomplishmentKind', 'CodeCompliance', 'DualWitnessStatus', 'FailureObstructionItem', 'GateStatus', 'IntelligenceCollectionPort', 'IntelligenceCollectionReceipt', 'IntelligenceDigestionFileSystemPort', 'IntelligenceLifecyclePort', 'NaturalScienceGates', 'OMCMonographAuditRecord', 'OMCPRReviewRecord', 'OMCRecord', 'OMCRecordType', 'OMCSubsystemAuditRecord', 'OMCVerdict', 'ObstructionKind', 'PaperReviewDigestRecord', 'RecordType', 'ReviewStatus', 'ReviewSummary', 'Severity', 'parse_omc_dict', 'parse_omc_line', 'parse_omc_markdown']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CodeCompliance': ('.omc_dag_models', 'CodeCompliance'),
    'DualWitnessStatus': ('.omc_dag_models', 'DualWitnessStatus'),
    'GateStatus': ('.omc_dag_models', 'GateStatus'),
    'NaturalScienceGates': ('.omc_dag_models', 'NaturalScienceGates'),
    'OMCMonographAuditRecord': ('.omc_dag_models', 'OMCMonographAuditRecord'),
    'OMCPRReviewRecord': ('.omc_dag_models', 'OMCPRReviewRecord'),
    'OMCRecord': ('.omc_dag_models', 'OMCRecord'),
    'OMCRecordType': ('.omc_dag_models', 'OMCRecordType'),
    'OMCSubsystemAuditRecord': ('.omc_dag_models', 'OMCSubsystemAuditRecord'),
    'OMCVerdict': ('.omc_dag_models', 'OMCVerdict'),
    'parse_omc_dict': ('.omc_dag_models', 'parse_omc_dict'),
    'parse_omc_line': ('.omc_dag_models', 'parse_omc_line'),
    'parse_omc_markdown': ('.omc_dag_models', 'parse_omc_markdown'),
    'AccomplishmentItem': ('.paper_review_models', 'AccomplishmentItem'),
    'AccomplishmentKind': ('.paper_review_models', 'AccomplishmentKind'),
    'FailureObstructionItem': ('.paper_review_models', 'FailureObstructionItem'),
    'ObstructionKind': ('.paper_review_models', 'ObstructionKind'),
    'PaperReviewDigestRecord': ('.paper_review_models', 'PaperReviewDigestRecord'),
    'RecordType': ('.paper_review_models', 'RecordType'),
    'ReviewStatus': ('.paper_review_models', 'ReviewStatus'),
    'ReviewSummary': ('.paper_review_models', 'ReviewSummary'),
    'Severity': ('.paper_review_models', 'Severity'),
    'IntelligenceCollectionPort': ('.ports', 'IntelligenceCollectionPort'),
    'IntelligenceCollectionReceipt': ('.ports', 'IntelligenceCollectionReceipt'),
    'IntelligenceDigestionFileSystemPort': ('.ports', 'IntelligenceDigestionFileSystemPort'),
    'IntelligenceLifecyclePort': ('.ports', 'IntelligenceLifecyclePort'),
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
