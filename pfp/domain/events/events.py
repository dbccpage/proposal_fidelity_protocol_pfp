"""Domain Events for the Symbol Game Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base immutable domain event."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    aggregate_id: str = ""
    aggregate_type: str = ""
    authority_effect: str = "None"


@dataclass(frozen=True, slots=True)
class TurnExecutedEvent(DomainEvent):
    """Raised when a sparse manifold retraction turn is executed.

    ``l1_obstruction`` is ``None`` when the turn measured no L1 obstruction.
    A simplicial retraction measures the cycle holonomy sum over one chosen
    cycle basis instead; that value depends on the basis, so it is published
    exactly, as ``holonomy_sum``, and never as ``l1_obstruction``.
    """

    task_id: str = ""
    step_id: str = ""
    purity: float = 0.0
    l1_obstruction: float | None = None
    holonomy_sum: Fraction | None = None
    is_exact: bool = False
    verdict: str = ""
    aggregate_type: str = "LlmTurnRunRoot"

    def __post_init__(self) -> None:
        if self.holonomy_sum is not None and type(self.holonomy_sum) is not Fraction:
            raise TypeError("holonomy_sum must be an exact Fraction or None")


@dataclass(frozen=True, slots=True)
class ProposalEvaluatedEvent(DomainEvent):
    """Raised when a candidate repair proposal is evaluated."""

    proposal_id: str = ""
    is_admissible: bool = True
    efficiency: float = 0.0
    kill_reason: str = "None"
    aggregate_type: str = "CandidateProposal"


@dataclass(frozen=True, slots=True)
class RunRootCreatedEvent(DomainEvent):
    """Raised when a new problem run root is initialized."""

    run_root_id: str = ""
    task_id: str = ""
    objective: str = ""
    candidate_budget: int = 4
    operation_budget: int = 16
    aggregate_type: str = "RunRoot"


@dataclass(frozen=True, slots=True)
class ObstructionEliminatedEvent(DomainEvent):
    """Raised when an obstruction is eliminated via retraction."""

    obstruction_id: str = ""
    elimination_receipt_id: str = ""
    aggregate_type: str = "PromptArtifact"


@dataclass(frozen=True, slots=True)
class CorpusFrozenEvent(DomainEvent):
    """Raised when a dataset corpus is cryptographically frozen."""

    corpus_id: str = ""
    digest: str = ""
    aggregate_type: str = "FrozenCorpus"
