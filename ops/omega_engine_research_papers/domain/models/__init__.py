"""Paper specification, claim ledger, and monograph data structures."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .anti_skills import ACTIVE_ANTI_SKILLS, AntiSkillDefinition, get_anti_skill_by_id, get_anti_skill_by_number, total_anti_skills_count
    from .bibliography import BibEntry, CitationGraph, LiteratureSpineRef
    from .claim_ledger import ClaimLedger, ClaimRecord, ClaimStatus, ClaimVerificationReceipt
    from .paper_spec import EADCAddress, MonographEnvelope, PaperSpecification, Section
    from .republication_checklist import CATALOG_ORIGIN, CATALOG_VERSION, EVIDENCE_CHANNELS, REPUBLICATION_CATALOG, RepublicationCheckItem, RepublicationGateReceipt

__all__ = ['EADCAddress', 'Section', 'MonographEnvelope', 'PaperSpecification', 'ClaimStatus', 'ClaimRecord', 'ClaimLedger', 'ClaimVerificationReceipt', 'BibEntry', 'CitationGraph', 'LiteratureSpineRef', 'CATALOG_VERSION', 'CATALOG_ORIGIN', 'REPUBLICATION_CATALOG', 'EVIDENCE_CHANNELS', 'RepublicationCheckItem', 'RepublicationGateReceipt', 'AntiSkillDefinition', 'ACTIVE_ANTI_SKILLS', 'get_anti_skill_by_id', 'get_anti_skill_by_number', 'total_anti_skills_count']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ACTIVE_ANTI_SKILLS': ('.anti_skills', 'ACTIVE_ANTI_SKILLS'),
    'AntiSkillDefinition': ('.anti_skills', 'AntiSkillDefinition'),
    'get_anti_skill_by_id': ('.anti_skills', 'get_anti_skill_by_id'),
    'get_anti_skill_by_number': ('.anti_skills', 'get_anti_skill_by_number'),
    'total_anti_skills_count': ('.anti_skills', 'total_anti_skills_count'),
    'BibEntry': ('.bibliography', 'BibEntry'),
    'CitationGraph': ('.bibliography', 'CitationGraph'),
    'LiteratureSpineRef': ('.bibliography', 'LiteratureSpineRef'),
    'ClaimLedger': ('.claim_ledger', 'ClaimLedger'),
    'ClaimRecord': ('.claim_ledger', 'ClaimRecord'),
    'ClaimStatus': ('.claim_ledger', 'ClaimStatus'),
    'ClaimVerificationReceipt': ('.claim_ledger', 'ClaimVerificationReceipt'),
    'EADCAddress': ('.paper_spec', 'EADCAddress'),
    'MonographEnvelope': ('.paper_spec', 'MonographEnvelope'),
    'PaperSpecification': ('.paper_spec', 'PaperSpecification'),
    'Section': ('.paper_spec', 'Section'),
    'CATALOG_ORIGIN': ('.republication_checklist', 'CATALOG_ORIGIN'),
    'CATALOG_VERSION': ('.republication_checklist', 'CATALOG_VERSION'),
    'EVIDENCE_CHANNELS': ('.republication_checklist', 'EVIDENCE_CHANNELS'),
    'REPUBLICATION_CATALOG': ('.republication_checklist', 'REPUBLICATION_CATALOG'),
    'RepublicationCheckItem': ('.republication_checklist', 'RepublicationCheckItem'),
    'RepublicationGateReceipt': ('.republication_checklist', 'RepublicationGateReceipt'),
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
