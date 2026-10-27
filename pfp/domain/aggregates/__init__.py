"""Aggregates for the Symbol Game bounded context."""

from __future__ import annotations

from .code_change_run_root import CodeChangeRunRootV1
from .learning_policy import (
    FrozenCorpus,
    PolicyScore,
    PolicySearchSolver,
    RoutingHypothesis,
    RoutingPolicyProjector,
    SelfImprovementReceipt,
)
from .llm_turn_run_root import LlmTurnRunRootV1
from .prompt_artifact import PromptArtifactV1
from .research_claim import ResearchClaimV1
from .research_run_root import ResearchRunRootV1

# Compatibility aliases
CodeChangeRunRoot = CodeChangeRunRootV1
LLMTurnRunRoot = LlmTurnRunRootV1
PromptArtifact = PromptArtifactV1
ResearchClaim = ResearchClaimV1
ResearchRunRoot = ResearchRunRootV1
LearningPolicy = PolicySearchSolver

__all__ = [
    "CodeChangeRunRoot",
    "CodeChangeRunRootV1",
    "FrozenCorpus",
    "LLMTurnRunRoot",
    "LearningPolicy",
    "LlmTurnRunRootV1",
    "PolicyScore",
    "PolicySearchSolver",
    "PromptArtifact",
    "PromptArtifactV1",
    "ResearchClaim",
    "ResearchClaimV1",
    "ResearchRunRoot",
    "ResearchRunRootV1",
    "RoutingHypothesis",
    "RoutingPolicyProjector",
    "SelfImprovementReceipt",
]


_PFP_EXPORTS = {'AggregateRoot': ('pfp.domain.aggregates.base', 'AggregateRoot'), 'CycleBalanceQuartetAggregate': ('pfp.domain.aggregates.cycle_balance_aggregate', 'CycleBalanceQuartetAggregate'), 'PilotAggregate': ('pfp.domain.aggregates.pilot_aggregate', 'PilotAggregate'), 'SpanPartitionAggregate': ('pfp.domain.aggregates.rewriting_aggregate', 'SpanPartitionAggregate')}
__all__ = list(dict.fromkeys([*__all__, *_PFP_EXPORTS]))

def __getattr__(name: str):
    from importlib import import_module
    if name not in _PFP_EXPORTS:
        raise AttributeError(name)
    module, attribute = _PFP_EXPORTS[name]
    value = getattr(import_module(module), attribute)
    globals()[name] = value
    return value
