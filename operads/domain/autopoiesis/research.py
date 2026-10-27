"""Evidence-bound experimental re-entry contracts; no production admission."""

from dataclasses import dataclass
import json
from typing import Protocol

from operads.domain.autopoiesis.learning import digest


ALLOWED_FILES = frozenset({"prompt.txt", "workflow.json", "search_policy.py", "context_policy.py"})
PHASE_CAPS = {
    "preflight": 2_000_000,
    "discovery": 16_000_000,
    "transfer": 10_000_000,
    "ablations": 6_000_000,
    "ignition": 4_000_000,
    "retry": 2_000_000,
}


def require_digest(value):
    if (
        type(value) is not str
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError("INVALID_DIGEST")


@dataclass(frozen=True)
class HarnessCandidateV1:
    source: str
    parent: str
    files: tuple[tuple[str, str], ...]
    strategy: str
    mutation: str
    schema: str = "oeop.harness-candidate.v1"

    def __post_init__(self):
        require_digest(self.source)
        require_digest(self.parent)
        if self.schema != "oeop.harness-candidate.v1" or any(
            type(v) is not str or not v.strip() or len(v) > 1024
            for v in (self.strategy, self.mutation)
        ):
            raise ValueError("INVALID_CANDIDATE")
        if type(self.files) is not tuple or set(k for k, _ in self.files) != ALLOWED_FILES:
            raise ValueError("CANDIDATE_EDIT_SURFACE")
        if len(self.files) != len(ALLOWED_FILES):
            raise ValueError("DUPLICATE_PATH")
        if any(
            type(v) is not str or not v.strip() or len(v.encode()) > 16384 for _, v in self.files
        ):
            raise ValueError("CANDIDATE_FILE_BOUND")
        if len(json.dumps(dict(self.files), sort_keys=True)) > 3600:
            raise ValueError("CANDIDATE_REENTRY_CONTEXT_BOUND")

    @property
    def candidate_id(self):
        return digest(self.to_dict())

    def to_dict(self):
        return {
            "schema": self.schema,
            "source": self.source,
            "parent": self.parent,
            "files": dict(self.files),
            "strategy": self.strategy,
            "mutation": self.mutation,
        }

    @classmethod
    def from_dict(cls, value):
        if (
            type(value) is not dict
            or set(value) != {"schema", "source", "parent", "files", "strategy", "mutation"}
            or type(value["files"]) is not dict
        ):
            raise ValueError("CANDIDATE_FIELDS")
        return cls(**{**value, "files": tuple(sorted(value["files"].items()))})


@dataclass(frozen=True)
class ExperimentSpecV1:
    campaign_id: str
    source: str
    checker: str
    split: str
    budget_id: str
    configuration: str
    inner_model: str = "claude-haiku-5-5"
    outer_model: str = "claude-sonnet-5-5"
    ceiling: int = 40_000_000
    schema: str = "oeop.harness-experiment.v1"

    def __post_init__(self):
        for value in (self.source, self.checker, self.split, self.configuration):
            require_digest(value)
        if self.schema != "oeop.harness-experiment.v1":
            raise ValueError("EXPERIMENT_SCHEMA")
        if (
            type(self.campaign_id) is not str
            or not self.campaign_id
            or self.budget_id != self.campaign_id
        ):
            raise ValueError("ORIGINAL_BUDGET_REQUIRED")
        if type(self.ceiling) is not int or self.ceiling != sum(PHASE_CAPS.values()):
            raise ValueError("CAMPAIGN_CEILING_FIXED")
        if (self.inner_model, self.outer_model) != ("claude-haiku-5-5", "claude-sonnet-5-5"):
            raise ValueError("CAMPAIGN_MODELS_FIXED")

    def to_dict(self):
        return dict(vars(self))

    @property
    def experiment_id(self):
        return digest(self.to_dict())


@dataclass(frozen=True)
class EvaluationReceiptV1:
    experiment: str
    source: str
    candidate: str
    parent: str
    checker: str
    split: str
    model: str
    configuration: str
    budget_id: str
    occurrence: str
    task: str
    family: str
    phase: str
    repetition: int
    reply: str
    public_pass: bool
    private_pass: bool
    status: str
    cost: int
    evidence: tuple[str, ...]
    schema: str = "oeop.harness-evaluation.v1"

    def __post_init__(self):
        if self.schema != "oeop.harness-evaluation.v1" or self.phase not in PHASE_CAPS:
            raise ValueError("EVALUATION_SCHEMA_OR_PHASE")
        if any(
            type(v) is not str or not v
            for v in (self.model, self.budget_id, self.occurrence, self.task, self.family)
        ):
            raise ValueError("EVALUATION_IDENTITY_REQUIRED")
        if type(self.evidence) is not tuple:
            raise ValueError("EVIDENCE_TUPLE_REQUIRED")
        for ref in self.evidence:
            require_digest(ref)
        for name in (
            "experiment",
            "source",
            "candidate",
            "parent",
            "checker",
            "split",
            "configuration",
            "reply",
        ):
            require_digest(getattr(self, name))
        for name in ("public_pass", "private_pass"):
            if type(getattr(self, name)) is not bool:
                raise ValueError("EXACT_BOOLEAN_REQUIRED")
        if (
            type(self.cost) is not int
            or self.cost < 0
            or type(self.repetition) is not int
            or self.repetition < 0
        ):
            raise ValueError("EXACT_NONNEGATIVE_REQUIRED")
        if self.status not in (
            "HOST_ACCEPTED",
            "TYPED_REFUSAL",
            "EXECUTION_ERROR",
            "INFRASTRUCTURE_ERROR",
            "INCOMPLETE",
            "FIXTURE_VERIFIED",
        ):
            raise ValueError("EVALUATION_STATUS")
        if self.private_pass and (
            not self.evidence or self.status not in ("HOST_ACCEPTED", "FIXTURE_VERIFIED")
        ):
            raise ValueError("SUCCESS_REQUIRES_MEASURED_EVIDENCE")

    @property
    def receipt_id(self):
        return digest(self.to_dict())

    def to_dict(self):
        return {**vars(self), "evidence": list(self.evidence)}


@dataclass(frozen=True)
class IncumbentDecisionV1:
    experiment: str
    previous: str
    proposed: str
    selected: str
    selection: tuple[str, ...]
    confirmation: tuple[str, ...]
    reason: str
    schema: str = "oeop.harness-incumbent.v1"

    def __post_init__(self):
        if self.schema != "oeop.harness-incumbent.v1" or self.reason not in (
            "CONFIRMED_IMPROVEMENT",
            "RETAIN_INCUMBENT",
        ):
            raise ValueError("DECISION_SCHEMA_OR_REASON")
        for group in (self.selection, self.confirmation):
            if type(group) is not tuple:
                raise ValueError("DECISION_EVIDENCE_TUPLE_REQUIRED")
            for ref in group:
                require_digest(ref)
        for name in ("experiment", "previous", "proposed", "selected"):
            require_digest(getattr(self, name))
        if self.selected not in (self.previous, self.proposed):
            raise ValueError("FOREIGN_INCUMBENT")
        if self.selected != self.previous and (not self.selection or not self.confirmation):
            raise ValueError("FRESH_CONFIRMATION_REQUIRED")


class ResearchEvaluationPort(Protocol):
    def evaluate(
        self, candidate: HarnessCandidateV1, *, panel: str, occurrence: str, phase: str
    ) -> tuple[EvaluationReceiptV1, ...]: ...


class ResearchWorkspacePort(Protocol):
    def retain(self, candidate: HarnessCandidateV1) -> str: ...
    def load(self, candidate_id: str) -> HarnessCandidateV1: ...


class ResearchProposalPort(Protocol):
    def propose(
        self,
        incumbent: HarnessCandidateV1,
        *,
        occurrence: str,
        evidence: tuple[EvaluationReceiptV1, ...],
        phase: str,
    ) -> HarnessCandidateV1: ...
