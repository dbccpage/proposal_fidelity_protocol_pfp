"""Serial qualification ladder for the Adversary engineering factory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adversary.stage.domain import ValuationReceiptV1
from adversary.stage.domain.canonical import (
    AUTHORITY_EFFECT_NONE,
    digest,
    exact_bool,
    identifier,
    integer,
    semantic_id,
    string_tuple,
    text,
)

from .models import (
    ANTI_SKILL_STAGE_ORDER,
    ANTI_SKILL_STAGES,
    AntiSkillGateReceiptV1,
    CalibrationReceiptV1,
    PredictionReceiptV1,
)

QUALIFICATION_LEVELS = ("N1", "N2", "N4")


@dataclass(frozen=True, slots=True)
class ParallelCriticFindingV1:
    finding_key: str
    critic_agent_id: str
    statement: str
    evidence_ref: str
    blocking: bool
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.parallel-critic-finding.v1"
    finding_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.finding_key, "finding_key")
        identifier(self.critic_agent_id, "critic_agent_id")
        text(self.statement, "statement")
        digest(self.evidence_ref, "evidence_ref")
        exact_bool(self.blocking, "blocking")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("critic finding authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.parallel-critic-finding.v1":
            raise ValueError("unsupported parallel critic finding schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.finding_id and self.finding_id != expected:
            raise ValueError("finding_id does not match canonical content")
        object.__setattr__(self, "finding_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "finding_key": self.finding_key,
            "critic_agent_id": self.critic_agent_id,
            "statement": self.statement,
            "evidence_ref": self.evidence_ref,
            "blocking": self.blocking,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "finding_id": self.finding_id}


def aggregate_parallel_findings(
    findings: tuple[ParallelCriticFindingV1, ...],
) -> tuple[ParallelCriticFindingV1, ...]:
    """Canonical order independent of worker completion order; no laundering."""

    if type(findings) is not tuple or any(
        type(item) is not ParallelCriticFindingV1 for item in findings
    ):
        raise TypeError("findings must be an exact typed tuple")
    if len({item.finding_id for item in findings}) != len(findings):
        raise ValueError("exact duplicate critic findings are refused")
    by_key: dict[str, ParallelCriticFindingV1] = {}
    for finding in findings:
        prior = by_key.get(finding.finding_key)
        if prior is not None and prior.to_dict() != finding.to_dict():
            raise ValueError("conflicting duplicate finding keys are refused")
        by_key[finding.finding_key] = finding
    return tuple(
        sorted(
            by_key.values(),
            key=lambda item: (
                item.finding_key,
                item.critic_agent_id,
                item.evidence_ref,
            ),
        )
    )


@dataclass(frozen=True, slots=True)
class QualificationReceiptV1:
    level: str
    worker_count: int
    evidence_refs: tuple[str, ...]
    deterministic_replay: bool
    independent_critics: bool
    completion_order_independent: bool
    budget_gate: bool
    race_gate: bool
    duplicate_finding_gate: bool
    passed: bool
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.qualification-receipt.v1"
    receipt_id: str = ""

    def __post_init__(self) -> None:
        if self.level not in QUALIFICATION_LEVELS:
            raise ValueError("qualification level is not closed")
        expected_workers = {"N1": 1, "N2": 2, "N4": 4}[self.level]
        integer(self.worker_count, "worker_count", minimum=1, maximum=4)
        if self.worker_count != expected_workers:
            raise ValueError("qualification worker count differs from its level")
        object.__setattr__(
            self,
            "evidence_refs",
            string_tuple(self.evidence_refs, "evidence_refs", digests=True),
        )
        if not self.evidence_refs:
            raise ValueError("qualification requires evidence")
        for field in (
            "deterministic_replay",
            "independent_critics",
            "completion_order_independent",
            "budget_gate",
            "race_gate",
            "duplicate_finding_gate",
            "passed",
        ):
            exact_bool(getattr(self, field), field)
        required = {
            "N1": self.deterministic_replay,
            "N2": (
                self.deterministic_replay
                and self.independent_critics
                and self.completion_order_independent
            ),
            "N4": (
                self.deterministic_replay
                and self.independent_critics
                and self.completion_order_independent
                and self.budget_gate
                and self.race_gate
                and self.duplicate_finding_gate
            ),
        }[self.level]
        if self.passed != required:
            raise ValueError("qualification PASS is not independently derived")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("qualification authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.qualification-receipt.v1":
            raise ValueError("unsupported qualification receipt schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.receipt_id and self.receipt_id != expected:
            raise ValueError("receipt_id does not match canonical content")
        object.__setattr__(self, "receipt_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "worker_count": self.worker_count,
            "evidence_refs": list(self.evidence_refs),
            "deterministic_replay": self.deterministic_replay,
            "independent_critics": self.independent_critics,
            "completion_order_independent": self.completion_order_independent,
            "budget_gate": self.budget_gate,
            "race_gate": self.race_gate,
            "duplicate_finding_gate": self.duplicate_finding_gate,
            "passed": self.passed,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "receipt_id": self.receipt_id}


def qualification_receipt_v1(
    *,
    level: str,
    evidence_refs: tuple[str, ...],
    deterministic_replay: bool,
    independent_critics: bool = False,
    completion_order_independent: bool = False,
    budget_gate: bool = False,
    race_gate: bool = False,
    duplicate_finding_gate: bool = False,
) -> QualificationReceiptV1:
    required = {
        "N1": deterministic_replay,
        "N2": (
            deterministic_replay
            and independent_critics
            and completion_order_independent
        ),
        "N4": (
            deterministic_replay
            and independent_critics
            and completion_order_independent
            and budget_gate
            and race_gate
            and duplicate_finding_gate
        ),
    }
    if level not in required:
        raise ValueError("qualification level is not closed")
    return QualificationReceiptV1(
        level=level,
        worker_count={"N1": 1, "N2": 2, "N4": 4}[level],
        evidence_refs=evidence_refs,
        deterministic_replay=deterministic_replay,
        independent_critics=independent_critics,
        completion_order_independent=completion_order_independent,
        budget_gate=budget_gate,
        race_gate=race_gate,
        duplicate_finding_gate=duplicate_finding_gate,
        passed=required[level],
    )


@dataclass(frozen=True, slots=True)
class QualificationLadderV1:
    receipts: tuple[QualificationReceiptV1, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.qualification-ladder.v1"
    ladder_id: str = ""

    def __post_init__(self) -> None:
        if type(self.receipts) is not tuple or any(
            type(item) is not QualificationReceiptV1 for item in self.receipts
        ):
            raise TypeError("qualification receipts must be an exact typed tuple")
        levels = tuple(item.level for item in self.receipts)
        if levels != QUALIFICATION_LEVELS[: len(levels)]:
            raise ValueError("qualification levels must form the serial prefix")
        if any(not item.passed for item in self.receipts):
            raise ValueError("a failed level cannot enter the qualification ladder")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("qualification ladder authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.qualification-ladder.v1":
            raise ValueError("unsupported qualification ladder schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.ladder_id and self.ladder_id != expected:
            raise ValueError("ladder_id does not match canonical content")
        object.__setattr__(self, "ladder_id", expected)

    @property
    def qualified_for_supervised_run(self) -> bool:
        return tuple(item.level for item in self.receipts) == QUALIFICATION_LEVELS

    def _payload(self) -> dict[str, Any]:
        return {
            "receipts": [item.to_dict() for item in self.receipts],
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._payload(),
            "qualified_for_supervised_run": self.qualified_for_supervised_run,
            "ladder_id": self.ladder_id,
        }


@dataclass(frozen=True, slots=True)
class SupervisedEngineeringPacketV1:
    qualification_ladder: QualificationLadderV1
    isolated_worktree_ref: str
    patch_ref: str
    test_refs: tuple[str, ...]
    finding_refs: tuple[str, ...]
    valuation: ValuationReceiptV1
    prediction: PredictionReceiptV1
    calibration: CalibrationReceiptV1
    anti_skill_gates: tuple[AntiSkillGateReceiptV1, ...]
    uns_ref: str
    jsonl_ref: str
    draft_pr_text: str
    publication_status: str = "DRAFT_ONLY"
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.supervised-engineering-packet.v1"
    packet_id: str = ""

    def __post_init__(self) -> None:
        if type(self.qualification_ladder) is not QualificationLadderV1:
            raise TypeError("qualification_ladder must be exact QualificationLadderV1")
        if not self.qualification_ladder.qualified_for_supervised_run:
            raise ValueError("supervised packet requires the completed serial ladder")
        for field in (
            "isolated_worktree_ref",
            "patch_ref",
            "uns_ref",
            "jsonl_ref",
        ):
            digest(getattr(self, field), field)
        for field in ("test_refs", "finding_refs"):
            object.__setattr__(
                self,
                field,
                string_tuple(getattr(self, field), field, digests=True),
            )
        if not self.test_refs:
            raise ValueError("supervised packet requires test evidence")
        if type(self.valuation) is not ValuationReceiptV1:
            raise TypeError("valuation must be exact ValuationReceiptV1")
        if self.valuation.delta_phi > 0:
            raise ValueError("an increasing-Phi patch cannot enter qualification")
        if (
            type(self.prediction) is not PredictionReceiptV1
            or type(self.calibration) is not CalibrationReceiptV1
        ):
            raise TypeError("prediction and calibration must be exact typed receipts")
        if self.calibration.prediction_id != self.prediction.prediction_id:
            raise ValueError("supervised calibration names another prediction")
        if type(self.anti_skill_gates) is not tuple or any(
            type(item) is not AntiSkillGateReceiptV1 for item in self.anti_skill_gates
        ):
            raise TypeError("anti_skill_gates must be an exact typed tuple")
        if {item.stage for item in self.anti_skill_gates} != ANTI_SKILL_STAGES or any(
            item.disposition != "CLEAR" for item in self.anti_skill_gates
        ):
            raise ValueError("all three anti-skill loci must clear")
        if (
            tuple(item.stage for item in self.anti_skill_gates)
            != ANTI_SKILL_STAGE_ORDER
        ):
            raise ValueError("anti-skill gates are not in canonical lifecycle order")
        text(self.draft_pr_text, "draft_pr_text")
        if self.publication_status != "DRAFT_ONLY":
            raise ValueError("supervised qualification cannot publish")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("supervised packet authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.supervised-engineering-packet.v1":
            raise ValueError("unsupported supervised engineering packet schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.packet_id and self.packet_id != expected:
            raise ValueError("packet_id does not match canonical content")
        object.__setattr__(self, "packet_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "qualification_ladder": self.qualification_ladder.to_dict(),
            "isolated_worktree_ref": self.isolated_worktree_ref,
            "patch_ref": self.patch_ref,
            "test_refs": list(self.test_refs),
            "finding_refs": list(self.finding_refs),
            "valuation": self.valuation.to_dict(),
            "prediction": self.prediction.to_dict(),
            "calibration": self.calibration.to_dict(),
            "anti_skill_gates": [item.to_dict() for item in self.anti_skill_gates],
            "uns_ref": self.uns_ref,
            "jsonl_ref": self.jsonl_ref,
            "draft_pr_text": self.draft_pr_text,
            "publication_status": self.publication_status,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "packet_id": self.packet_id}


def build_supervised_engineering_packet_v1(
    *,
    ladder: QualificationLadderV1,
    isolated_worktree_ref: str,
    patch_ref: str,
    test_refs: tuple[str, ...],
    finding_refs: tuple[str, ...],
    valuation: ValuationReceiptV1,
    prediction: PredictionReceiptV1,
    calibration: CalibrationReceiptV1,
    anti_skill_gates: tuple[AntiSkillGateReceiptV1, ...],
    uns_ref: str,
    jsonl_ref: str,
    draft_pr_text: str,
) -> SupervisedEngineeringPacketV1:
    if type(ladder) is not QualificationLadderV1:
        raise TypeError("ladder must be exact QualificationLadderV1")
    if not ladder.qualified_for_supervised_run:
        raise ValueError("N1, N2, and N4 must pass before the supervised run")
    return SupervisedEngineeringPacketV1(
        qualification_ladder=ladder,
        isolated_worktree_ref=isolated_worktree_ref,
        patch_ref=patch_ref,
        test_refs=test_refs,
        finding_refs=finding_refs,
        valuation=valuation,
        prediction=prediction,
        calibration=calibration,
        anti_skill_gates=anti_skill_gates,
        uns_ref=uns_ref,
        jsonl_ref=jsonl_ref,
        draft_pr_text=draft_pr_text,
    )


__all__ = [
    "QUALIFICATION_LEVELS",
    "ParallelCriticFindingV1",
    "QualificationLadderV1",
    "QualificationReceiptV1",
    "SupervisedEngineeringPacketV1",
    "aggregate_parallel_findings",
    "build_supervised_engineering_packet_v1",
    "qualification_receipt_v1",
]
