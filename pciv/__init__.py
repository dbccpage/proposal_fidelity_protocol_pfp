"""pciv

Sovereign Clean Architecture package for Prompt Civilization, Lamarckian Retro-Inheritance,
Lineage DAGs, Genetic Prompt Forge, Demographic Reserves, and Epistemic Immunity Gatekeeping.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .domain.elenchus import ElenchusResult, SocraticElenchusBureau
    from .domain.models import AntibodyEntryV1, CemeteryHeadstoneV1, CivilizationPrompt, CivilizationState, CustodyTier, DomainPlacementV1, ExecutionOccurrenceV1, GenealogyEntryV1, PopulationTier, PromotionDecision, PromptGenomeV1, PromptPerception, PromptViewV1, ProtectedSpanV1, UnauthorizedAdmissionError, hard_domain_eligible
    from .domain.lamarckian import CochainResidualV1, LamarckianMutationReceiptV1
    from .domain.society import AggregateFitnessVectorV1, MigrationPolicyV1, PromptCivilizationV1, PromptSocietyV1
    from .controllers.prompt_civ_controller import PromptCivilizationController

__version__ = '0.1.0'

__all__ = ['AggregateFitnessVectorV1', 'AntibodyEntryV1', 'CemeteryHeadstoneV1', 'CivilizationPrompt', 'CivilizationState', 'CochainResidualV1', 'CustodyTier', 'DomainPlacementV1', 'ElenchusResult', 'ExecutionOccurrenceV1', 'GenealogyEntryV1', 'LamarckianMutationReceiptV1', 'MigrationPolicyV1', 'PopulationTier', 'PromotionDecision', 'PromptCivilizationController', 'PromptCivilizationV1', 'PromptGenomeV1', 'PromptPerception', 'PromptSocietyV1', 'PromptViewV1', 'ProtectedSpanV1', 'SocraticElenchusBureau', 'UnauthorizedAdmissionError', '__version__', 'hard_domain_eligible']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ElenchusResult': ('.domain.elenchus', 'ElenchusResult'),
    'SocraticElenchusBureau': ('.domain.elenchus', 'SocraticElenchusBureau'),
    'AntibodyEntryV1': ('.domain.models', 'AntibodyEntryV1'),
    'CemeteryHeadstoneV1': ('.domain.models', 'CemeteryHeadstoneV1'),
    'CivilizationPrompt': ('.domain.models', 'CivilizationPrompt'),
    'CivilizationState': ('.domain.models', 'CivilizationState'),
    'CustodyTier': ('.domain.models', 'CustodyTier'),
    'DomainPlacementV1': ('.domain.models', 'DomainPlacementV1'),
    'ExecutionOccurrenceV1': ('.domain.models', 'ExecutionOccurrenceV1'),
    'GenealogyEntryV1': ('.domain.models', 'GenealogyEntryV1'),
    'PopulationTier': ('.domain.models', 'PopulationTier'),
    'PromotionDecision': ('.domain.models', 'PromotionDecision'),
    'PromptGenomeV1': ('.domain.models', 'PromptGenomeV1'),
    'PromptPerception': ('.domain.models', 'PromptPerception'),
    'PromptViewV1': ('.domain.models', 'PromptViewV1'),
    'ProtectedSpanV1': ('.domain.models', 'ProtectedSpanV1'),
    'UnauthorizedAdmissionError': ('.domain.models', 'UnauthorizedAdmissionError'),
    'hard_domain_eligible': ('.domain.models', 'hard_domain_eligible'),
    'CochainResidualV1': ('.domain.lamarckian', 'CochainResidualV1'),
    'LamarckianMutationReceiptV1': ('.domain.lamarckian', 'LamarckianMutationReceiptV1'),
    'AggregateFitnessVectorV1': ('.domain.society', 'AggregateFitnessVectorV1'),
    'MigrationPolicyV1': ('.domain.society', 'MigrationPolicyV1'),
    'PromptCivilizationV1': ('.domain.society', 'PromptCivilizationV1'),
    'PromptSocietyV1': ('.domain.society', 'PromptSocietyV1'),
    'PromptCivilizationController': ('.controllers.prompt_civ_controller', 'PromptCivilizationController'),
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
