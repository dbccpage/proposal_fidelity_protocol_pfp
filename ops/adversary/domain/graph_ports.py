"""Injected graph execution collaborators. AuthorityEffect: None."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from operations.domain.rop.result import Refusal, Result
from adversary.domain.evidence import CandidateCheckV1
from adversary.domain.graph_task import (
    GraphCandidateEvaluationV1,
    GraphTaskResultV1,
    GraphTaskV1,
)


class GraphCheckerPort(Protocol):
    def check(self, task: GraphTaskV1, candidate_bytes: bytes) -> CandidateCheckV1: ...


class GraphEvaluationPort(Protocol):
    def evaluate(
        self, task: GraphTaskV1, candidate_bytes: bytes, check: CandidateCheckV1
    ) -> Result[GraphCandidateEvaluationV1, Refusal]: ...

    def challenge(
        self, task: GraphTaskV1, evaluation: GraphCandidateEvaluationV1, challenge_bytes: bytes
    ) -> Result[bytes, Refusal]: ...


class GraphModelPort(Protocol):
    def propose(self, task: GraphTaskV1) -> Result[bytes, Refusal]:
        """Return a complete turn with actual request/output/validation bytes."""
        ...

    def critique(
        self, task: GraphTaskV1, evaluation: GraphCandidateEvaluationV1, round_index: int
    ) -> Result[bytes, Refusal]: ...


class GraphLearningPort(Protocol):
    def harvest(
        self,
        task: GraphTaskV1,
        evaluations: tuple[GraphCandidateEvaluationV1, ...],
        source_events: tuple[bytes, ...],
        challenges: tuple[bytes, ...],
    ) -> bytes: ...


@dataclass(frozen=True, slots=True)
class GraphRunReferenceV1:
    directory: str
    receipt_ref: str
    receipt_id: str
    result: GraphTaskResultV1


class GraphPersistencePort(Protocol):
    def persist(
        self, task: GraphTaskV1, result: GraphTaskResultV1
    ) -> Result[GraphRunReferenceV1, Refusal]: ...


class GraphExecutionPort(Protocol):
    def execute(self, task: GraphTaskV1, mode: str) -> Result[GraphRunReferenceV1, Refusal]: ...
