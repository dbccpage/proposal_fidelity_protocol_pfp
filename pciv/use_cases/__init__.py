"""Use cases layer for Prompt Civilization.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .ablation import BARRIERS, barrier_ablation_matrix
    from .backfill import HistoricalBackfillEngineV1, PromptCivBackfillEngineV1
    from .custody import PromptCustodyLedgerV1
    from .e2e import PromptCivE2EFixtureV1, PromptCivE2EHarnessV1
    from .fitness import ParetoFrontSelectorV1, PromptFitnessCalculatorV1
    from .forge import MutationOperatorCandidateV1, PopulationPolicyV1, PromptMutationEngineV1
    from .genealogy import LineageEdgeV1, LineageGraphV1, RelationshipType
    from .immunity import ArmedRepertoireManagerV1, ImmunityPropagationEngineV1
    from .integration import PromptCivIntegrationHarnessV1
    from .operator_custody import OperatorCustodyLifecycleV1
    from .prompt_ecology.ingest import PromptEcologyIngestUseCase, ingest_batch
    from .rank import AncestralRankCalculatorV1, RankCertificateVerifierV1
    from .view_engine import PromptGenomeRegistryV1, PromptViewEngineV1

__all__ = ['BARRIERS', 'AncestralRankCalculatorV1', 'ArmedRepertoireManagerV1', 'HistoricalBackfillEngineV1', 'ImmunityPropagationEngineV1', 'LineageEdgeV1', 'LineageGraphV1', 'MutationOperatorCandidateV1', 'OperatorCustodyLifecycleV1', 'ParetoFrontSelectorV1', 'PopulationPolicyV1', 'PromptCivBackfillEngineV1', 'PromptCivE2EFixtureV1', 'PromptCivE2EHarnessV1', 'PromptCivIntegrationHarnessV1', 'PromptCustodyLedgerV1', 'PromptEcologyIngestUseCase', 'PromptFitnessCalculatorV1', 'PromptGenomeRegistryV1', 'PromptMutationEngineV1', 'PromptViewEngineV1', 'RankCertificateVerifierV1', 'RelationshipType', 'barrier_ablation_matrix', 'ingest_batch']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'BARRIERS': ('.ablation', 'BARRIERS'),
    'barrier_ablation_matrix': ('.ablation', 'barrier_ablation_matrix'),
    'HistoricalBackfillEngineV1': ('.backfill', 'HistoricalBackfillEngineV1'),
    'PromptCivBackfillEngineV1': ('.backfill', 'PromptCivBackfillEngineV1'),
    'PromptCustodyLedgerV1': ('.custody', 'PromptCustodyLedgerV1'),
    'PromptCivE2EFixtureV1': ('.e2e', 'PromptCivE2EFixtureV1'),
    'PromptCivE2EHarnessV1': ('.e2e', 'PromptCivE2EHarnessV1'),
    'ParetoFrontSelectorV1': ('.fitness', 'ParetoFrontSelectorV1'),
    'PromptFitnessCalculatorV1': ('.fitness', 'PromptFitnessCalculatorV1'),
    'MutationOperatorCandidateV1': ('.forge', 'MutationOperatorCandidateV1'),
    'PopulationPolicyV1': ('.forge', 'PopulationPolicyV1'),
    'PromptMutationEngineV1': ('.forge', 'PromptMutationEngineV1'),
    'LineageEdgeV1': ('.genealogy', 'LineageEdgeV1'),
    'LineageGraphV1': ('.genealogy', 'LineageGraphV1'),
    'RelationshipType': ('.genealogy', 'RelationshipType'),
    'ArmedRepertoireManagerV1': ('.immunity', 'ArmedRepertoireManagerV1'),
    'ImmunityPropagationEngineV1': ('.immunity', 'ImmunityPropagationEngineV1'),
    'PromptCivIntegrationHarnessV1': ('.integration', 'PromptCivIntegrationHarnessV1'),
    'OperatorCustodyLifecycleV1': ('.operator_custody', 'OperatorCustodyLifecycleV1'),
    'PromptEcologyIngestUseCase': ('.prompt_ecology.ingest', 'PromptEcologyIngestUseCase'),
    'ingest_batch': ('.prompt_ecology.ingest', 'ingest_batch'),
    'AncestralRankCalculatorV1': ('.rank', 'AncestralRankCalculatorV1'),
    'RankCertificateVerifierV1': ('.rank', 'RankCertificateVerifierV1'),
    'PromptGenomeRegistryV1': ('.view_engine', 'PromptGenomeRegistryV1'),
    'PromptViewEngineV1': ('.view_engine', 'PromptViewEngineV1'),
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
