"""Evidence-bound learning contracts. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
import json
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass
from typing import Iterable, Protocol, Sequence

from .ports import ArtifactLocation, HarvestVaultPort


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def artifact_text_digest(raw: bytes) -> str:
    """Bind UTF-8 text while tolerating Git's Windows checkout line endings."""
    raw.decode("utf-8")
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


LEARNER_VERSION = "autop-learning-v1"
KINDS = frozenset({"RULE", "SKILL", "AGENT", "WORKFLOW", "CODE_GATE"})
OUTCOMES = frozenset({"NO_CHANGE", "BLOCKED", "FAILED", "VALIDATED"})


@dataclass(frozen=True)
class EvidenceSource:
    reference: str
    sha256: str


@dataclass(frozen=True)
class LearningEpisodeV1:
    host: str
    repository_revision: str
    terminal_outcome: str
    sources: tuple[EvidenceSource, ...]
    corrections: tuple[str, ...] = ()
    successes: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    origin: str = "session"
    schema: str = "omega.autopoiesis.learning-episode.v1"
    caller_configuration_reference: str | None = None
    caller_budget_reference: str | None = None

    @property
    def episode_id(self) -> str:
        # Paths are provenance, not identity: importing identical bytes twice
        # must not create another job merely because the export was renamed.
        return digest(
            {
                "sources": sorted(s.sha256 for s in self.sources),
                "revision": self.repository_revision,
                "origin": self.origin,
            }
        )

    def to_dict(self) -> dict:
        return asdict(self)


class ParentBudget(Protocol):
    @property
    def remaining_microusd(self) -> int: ...


@dataclass(frozen=True)
class CallerContext:
    provider: str
    model: str
    budget_reference: str
    budget: ParentBudget

    def require_available(self) -> None:
        if not self.provider or not self.model or not self.budget_reference:
            raise LearningBlocked("CALLER_CONFIGURATION_MISSING")
        if self.budget.remaining_microusd <= 0:
            raise LearningBlocked("PARENT_BUDGET_EXHAUSTED")


class LearningBlocked(RuntimeError):
    """A prerequisite or sufficient independent evidence is unavailable."""


@dataclass(frozen=True)
class FileChange:
    path: str
    content: str


@dataclass(frozen=True)
class LearningCandidate:
    kind: str
    artifact_id: str
    lesson: str
    rationale: str
    changes: tuple[FileChange, ...]
    evaluation_id: str
    motivating_case: str
    source_hashes: tuple[str, ...]
    trigger_terms: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in KINDS or not all(
            (self.artifact_id, self.lesson, self.evaluation_id, self.motivating_case)
        ):
            raise ValueError("invalid learning candidate")
        if not self.changes or len({c.path for c in self.changes}) != len(self.changes):
            raise ValueError("candidate needs unique file changes")
        if self.artifact_id not in {c.path for c in self.changes}:
            raise ValueError("artifact must be one of the changed files")
        if any(type(c.path) is not str or type(c.content) is not str for c in self.changes):
            raise ValueError("file changes must contain strings")
        prefixes = {
            "RULE": "omega_engine_operads/rules/",
            "SKILL": "omega_engine_operads/skills/",
            "AGENT": "omega_engine_operads/agents/",
            "WORKFLOW": "omega_engine_operads/domain/autopoiesis/profiles/",
        }
        if self.kind in prefixes and not self.artifact_id.startswith(prefixes[self.kind]):
            raise ValueError("artifact kind and canonical path disagree")
        if not self.trigger_terms or any(
            type(t) is not str or len(t.strip()) < 3 for t in self.trigger_terms
        ):
            raise ValueError("candidate needs explicit, nonempty retrieval trigger terms")

    @property
    def lesson_id(self) -> str:
        return digest({"kind": self.kind, "lesson": " ".join(self.lesson.casefold().split())})

    @property
    def candidate_id(self) -> str:
        content = asdict(self)
        # Additional sightings preserve new provenance without duplicating
        # an identical improvement bundle.
        content.pop("source_hashes")
        content.pop("rationale")
        return digest(content)


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    role: str  # motivating, applicable, non_applicable
    prompt: str
    expected: str


@dataclass(frozen=True)
class EvaluationObservation:
    output: str
    invoked: tuple[str, ...] = ()


class ProposerPort(Protocol):
    def propose(
        self,
        episode: LearningEpisodeV1,
        sources: dict[str, str],
        catalog: dict[str, str],
        context: CallerContext,
    ) -> LearningCandidate | None: ...


class EvaluationPort(Protocol):
    """Trusted evaluator, supplied independently of the candidate's edits."""

    evaluation_id: str
    model_dependent: bool
    cases: tuple[EvaluationCase, ...]
    allowed_paths: Sequence[str]

    def run(
        self,
        root: str,
        candidate: LearningCandidate,
        case: EvaluationCase,
        context: CallerContext,
        trial: int,
    ) -> EvaluationObservation: ...


class PublisherPort(Protocol):
    def publish(self, workspace: str, candidate: LearningCandidate, validation: dict) -> str: ...


@dataclass(frozen=True)
class ReviewedLesson:
    outcome: str
    url: str | None
    candidate_id: str


class LearningSessionPort(Protocol):
    """Learning bookkeeping in the current atomic store transaction."""

    def lookup_lesson(self, lesson_id: str) -> ReviewedLesson | None: ...

    def record_lesson(
        self, lesson_id: str, candidate_id: str, outcome: str, url: str | None = None
    ) -> None: ...

    def finish(self, job_id: str, receipt: dict) -> dict: ...


class LearningStorePort(Protocol):
    vault: HarvestVaultPort

    def enqueue(self, episode: LearningEpisodeV1) -> str: ...

    def serial(
        self, job_id: str, *, retry: bool = False
    ) -> AbstractContextManager[tuple[LearningSessionPort, dict | None]]: ...

    def finish_receipt(self, job_id: str, receipt: dict) -> dict: ...


class LearningWorkspacePort(Protocol):
    def catalog(
        self, episode: LearningEpisodeV1, *, allowed_paths: Iterable[str] = ()
    ) -> dict[str, str]: ...

    def prepare(
        self, job_id: str, candidate: LearningCandidate, suite: EvaluationPort
    ) -> ArtifactLocation: ...

    def apply(
        self, path: ArtifactLocation, candidate: LearningCandidate, suite: EvaluationPort
    ) -> str: ...

    def verify(self, path: ArtifactLocation, revision: str) -> None: ...
