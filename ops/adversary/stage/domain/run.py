"""Pure Adversary stage run state, terminal proposal, and replay receipt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import (
    AUTHORITY_EFFECT_NONE,
    digest,
    identifier,
    integer,
    semantic_id,
    string_tuple,
)
from .evaluation import ProgressMeasureV1
from .packets import AgentResultV1

RUN_TERMINALS = frozenset({"RUNNING", "COMPLETED", "HOLD", "REFUSE", "EXHAUSTED"})
SELECTION_DISPOSITIONS = frozenset({"SELECT", "HOLD", "REFUSE"})


@dataclass(frozen=True, slots=True)
class SceneVisitV1:
    scene_id: str
    count: int

    def __post_init__(self) -> None:
        identifier(self.scene_id, "scene_id")
        integer(self.count, "count", minimum=1, maximum=64)

    def to_dict(self) -> dict[str, Any]:
        return {"scene_id": self.scene_id, "count": self.count}


@dataclass(frozen=True, slots=True)
class SwarmRunStateV1:
    run_key: str
    profile_id: str
    current_scene_id: str
    visit_counts: tuple[SceneVisitV1, ...]
    result_ids: tuple[str, ...]
    progress_measure_ids: tuple[str, ...]
    remaining_budget: int
    scene_steps: int
    dry_rounds: int
    terminal_status: str = "RUNNING"
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.swarm-run-state.v1"
    state_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.run_key, "run_key")
        digest(self.profile_id, "profile_id")
        identifier(self.current_scene_id, "current_scene_id")
        if type(self.visit_counts) is not tuple or not self.visit_counts:
            raise TypeError("visit_counts must be a nonempty exact tuple")
        if any(type(item) is not SceneVisitV1 for item in self.visit_counts):
            raise TypeError("visit_counts contains a non-exact item")
        if (
            tuple(sorted(self.visit_counts, key=lambda item: item.scene_id))
            != self.visit_counts
        ):
            raise ValueError("visit counts must be sorted by scene_id")
        if len({item.scene_id for item in self.visit_counts}) != len(self.visit_counts):
            raise ValueError("visit counts must be unique")
        object.__setattr__(
            self,
            "result_ids",
            string_tuple(self.result_ids, "result_ids", digests=True, unique=False),
        )
        object.__setattr__(
            self,
            "progress_measure_ids",
            string_tuple(
                self.progress_measure_ids,
                "progress_measure_ids",
                digests=True,
                unique=False,
            ),
        )
        if len(self.result_ids) != len(self.progress_measure_ids):
            raise ValueError("run state result/progress arities differ")
        integer(self.remaining_budget, "remaining_budget")
        integer(self.scene_steps, "scene_steps")
        integer(self.dry_rounds, "dry_rounds")
        if self.terminal_status not in RUN_TERMINALS:
            raise ValueError("run terminal status is not closed")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("swarm run state authority_effect must be None")
        if self.schema_version != "core.oeas.swarm-run-state.v1":
            raise ValueError("unsupported swarm run state schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.state_id and self.state_id != expected:
            raise ValueError("state_id does not match canonical content")
        object.__setattr__(self, "state_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "run_key": self.run_key,
            "profile_id": self.profile_id,
            "current_scene_id": self.current_scene_id,
            "visit_counts": [item.to_dict() for item in self.visit_counts],
            "result_ids": list(self.result_ids),
            "progress_measure_ids": list(self.progress_measure_ids),
            "remaining_budget": self.remaining_budget,
            "scene_steps": self.scene_steps,
            "dry_rounds": self.dry_rounds,
            "terminal_status": self.terminal_status,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    @property
    def circuit_count(self) -> int:
        return len(self.result_ids)

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "state_id": self.state_id}


@dataclass(frozen=True, slots=True)
class CandidateSelectionProposalV1:
    selector_agent_id: str
    evaluator_epoch_id: str
    frontier_candidate_ids: tuple[str, ...]
    selected_candidate_id: str
    disposition: str
    evidence_refs: tuple[str, ...]
    nonclaims: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.candidate-selection-proposal.v1"
    proposal_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.selector_agent_id, "selector_agent_id")
        digest(self.evaluator_epoch_id, "evaluator_epoch_id")
        object.__setattr__(
            self,
            "frontier_candidate_ids",
            string_tuple(
                self.frontier_candidate_ids,
                "frontier_candidate_ids",
                digests=True,
            ),
        )
        if self.disposition not in SELECTION_DISPOSITIONS:
            raise ValueError("selection disposition is not closed")
        digest(self.selected_candidate_id, "selected_candidate_id", allow_empty=True)
        if self.disposition == "SELECT":
            if (
                not self.selected_candidate_id
                or self.selected_candidate_id not in self.frontier_candidate_ids
            ):
                raise ValueError("SELECT must name one frontier candidate")
        elif self.selected_candidate_id:
            raise ValueError("HOLD/REFUSE cannot name a selected candidate")
        object.__setattr__(
            self,
            "evidence_refs",
            string_tuple(self.evidence_refs, "evidence_refs", digests=True),
        )
        object.__setattr__(self, "nonclaims", string_tuple(self.nonclaims, "nonclaims"))
        if not self.evidence_refs or not self.nonclaims:
            raise ValueError("selection proposal requires evidence and nonclaims")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("selection proposal authority_effect must be None")
        if self.schema_version != "core.oeas.candidate-selection-proposal.v1":
            raise ValueError("unsupported selection proposal schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.proposal_id and self.proposal_id != expected:
            raise ValueError("proposal_id does not match canonical content")
        object.__setattr__(self, "proposal_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "selector_agent_id": self.selector_agent_id,
            "evaluator_epoch_id": self.evaluator_epoch_id,
            "frontier_candidate_ids": list(self.frontier_candidate_ids),
            "selected_candidate_id": self.selected_candidate_id,
            "disposition": self.disposition,
            "evidence_refs": list(self.evidence_refs),
            "nonclaims": list(self.nonclaims),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "proposal_id": self.proposal_id}


@dataclass(frozen=True, slots=True)
class SwarmRunReceiptV1:
    swarm_definition_id: str
    profile_id: str
    scene_graph_id: str
    initial_work_packet_id: str
    results: tuple[AgentResultV1, ...]
    progress_measures: tuple[ProgressMeasureV1, ...]
    causal_result_ids: tuple[str, ...]
    final_state: SwarmRunStateV1
    selection_proposal: CandidateSelectionProposalV1 | None = None
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.swarm-run-receipt.v1"
    terminal_cause: str = ""
    receipt_id: str = ""

    def __post_init__(self) -> None:
        for field in (
            "swarm_definition_id",
            "profile_id",
            "scene_graph_id",
            "initial_work_packet_id",
        ):
            digest(getattr(self, field), field)
        if type(self.results) is not tuple or any(
            type(item) is not AgentResultV1 for item in self.results
        ):
            raise TypeError("results must be an exact AgentResultV1 tuple")
        if type(self.progress_measures) is not tuple or any(
            type(item) is not ProgressMeasureV1 for item in self.progress_measures
        ):
            raise TypeError(
                "progress_measures must be an exact ProgressMeasureV1 tuple"
            )
        if len(self.results) != len(self.progress_measures):
            raise ValueError("receipt result/progress arities differ")
        object.__setattr__(
            self,
            "causal_result_ids",
            string_tuple(
                self.causal_result_ids,
                "causal_result_ids",
                digests=True,
                unique=False,
            ),
        )
        if self.causal_result_ids != tuple(result.result_id for result in self.results):
            raise ValueError("causal result order differs from stored results")
        if type(self.final_state) is not SwarmRunStateV1:
            raise TypeError("final_state must be exact SwarmRunStateV1")
        if self.final_state.result_ids != self.causal_result_ids:
            raise ValueError("final state and receipt causal results differ")
        if (
            self.selection_proposal is not None
            and type(self.selection_proposal) is not CandidateSelectionProposalV1
        ):
            raise TypeError("selection_proposal must be exact or None")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("swarm run receipt authority_effect must be None")
        if self.schema_version != "core.oeas.swarm-run-receipt.v1":
            raise ValueError("unsupported swarm run receipt schema")
        if type(self.terminal_cause) is not str or self.terminal_cause not in {
            "",
            "halt",
            "stall",
        }:
            raise ValueError("terminal_cause is not closed")
        expected = semantic_id(self.schema_version, self._payload())
        if self.receipt_id and self.receipt_id != expected:
            raise ValueError("receipt_id does not match canonical content")
        object.__setattr__(self, "receipt_id", expected)

    def _payload(self) -> dict[str, Any]:
        payload = {
            "swarm_definition_id": self.swarm_definition_id,
            "profile_id": self.profile_id,
            "scene_graph_id": self.scene_graph_id,
            "initial_work_packet_id": self.initial_work_packet_id,
            "results": [result.to_dict() for result in self.results],
            "progress_measures": [
                measure.to_dict() for measure in self.progress_measures
            ],
            "causal_result_ids": list(self.causal_result_ids),
            "final_state": self.final_state.to_dict(),
            "selection_proposal": (
                self.selection_proposal.to_dict()
                if self.selection_proposal is not None
                else None
            ),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }
        if self.terminal_cause:
            payload["terminal_cause"] = self.terminal_cause
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "receipt_id": self.receipt_id}


__all__ = [
    "CandidateSelectionProposalV1",
    "RUN_TERMINALS",
    "SceneVisitV1",
    "SwarmRunReceiptV1",
    "SwarmRunStateV1",
]
