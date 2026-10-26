"""Prompt Civilization domain layer.

Pure domain models, state machines, and ports. Zero external dependencies.
AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .elenchus import ElenchusResult, SocraticElenchusBureau
    from .models import AntibodyEntryV1, CemeteryHeadstoneV1, CivilizationPrompt, CivilizationState, CustodyTier, DomainPlacementV1, ExecutionOccurrenceV1, GenealogyEntryV1, PopulationTier, PromotionDecision, PromptGenomeV1, PromptPerception, PromptViewV1, ProtectedSpanV1, UnauthorizedAdmissionError, hard_domain_eligible
    from .lamarckian import CochainResidualV1, LamarckianMutationReceiptV1
    from .society import AggregateFitnessVectorV1, MigrationPolicyV1, PromptCivilizationV1, PromptSocietyV1
    from .ports import CemeterySink, ContentAddressedStoragePort, CustodyLedgerPort, EventLogPort, GenealogySink, GenealogyStorePort

__all__ = ['AggregateFitnessVectorV1', 'AntibodyEntryV1', 'CemeteryHeadstoneV1', 'CemeterySink', 'CivilizationPrompt', 'CivilizationState', 'CochainResidualV1', 'ContentAddressedStoragePort', 'CustodyLedgerPort', 'CustodyTier', 'DomainPlacementV1', 'ElenchusResult', 'EventLogPort', 'ExecutionOccurrenceV1', 'GenealogyEntryV1', 'GenealogySink', 'GenealogyStorePort', 'LamarckianMutationReceiptV1', 'MigrationPolicyV1', 'PopulationTier', 'PromotionDecision', 'PromptCivilizationV1', 'PromptGenomeV1', 'PromptPerception', 'PromptSocietyV1', 'PromptViewV1', 'ProtectedSpanV1', 'SocraticElenchusBureau', 'UnauthorizedAdmissionError', 'hard_domain_eligible']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ElenchusResult': ('.elenchus', 'ElenchusResult'),
    'SocraticElenchusBureau': ('.elenchus', 'SocraticElenchusBureau'),
    'AntibodyEntryV1': ('.models', 'AntibodyEntryV1'),
    'CemeteryHeadstoneV1': ('.models', 'CemeteryHeadstoneV1'),
    'CivilizationPrompt': ('.models', 'CivilizationPrompt'),
    'CivilizationState': ('.models', 'CivilizationState'),
    'CustodyTier': ('.models', 'CustodyTier'),
    'DomainPlacementV1': ('.models', 'DomainPlacementV1'),
    'ExecutionOccurrenceV1': ('.models', 'ExecutionOccurrenceV1'),
    'GenealogyEntryV1': ('.models', 'GenealogyEntryV1'),
    'PopulationTier': ('.models', 'PopulationTier'),
    'PromotionDecision': ('.models', 'PromotionDecision'),
    'PromptGenomeV1': ('.models', 'PromptGenomeV1'),
    'PromptPerception': ('.models', 'PromptPerception'),
    'PromptViewV1': ('.models', 'PromptViewV1'),
    'ProtectedSpanV1': ('.models', 'ProtectedSpanV1'),
    'UnauthorizedAdmissionError': ('.models', 'UnauthorizedAdmissionError'),
    'hard_domain_eligible': ('.models', 'hard_domain_eligible'),
    'CochainResidualV1': ('.lamarckian', 'CochainResidualV1'),
    'LamarckianMutationReceiptV1': ('.lamarckian', 'LamarckianMutationReceiptV1'),
    'AggregateFitnessVectorV1': ('.society', 'AggregateFitnessVectorV1'),
    'MigrationPolicyV1': ('.society', 'MigrationPolicyV1'),
    'PromptCivilizationV1': ('.society', 'PromptCivilizationV1'),
    'PromptSocietyV1': ('.society', 'PromptSocietyV1'),
    'CemeterySink': ('.ports', 'CemeterySink'),
    'ContentAddressedStoragePort': ('.ports', 'ContentAddressedStoragePort'),
    'CustodyLedgerPort': ('.ports', 'CustodyLedgerPort'),
    'EventLogPort': ('.ports', 'EventLogPort'),
    'GenealogySink': ('.ports', 'GenealogySink'),
    'GenealogyStorePort': ('.ports', 'GenealogyStorePort'),
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
