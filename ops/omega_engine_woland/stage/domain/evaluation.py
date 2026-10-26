"""Frozen evaluator epochs, valuations, progress, and stop laws for the Woland stage."""

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


@dataclass(frozen=True, slots=True)
class EvaluatorEpochV1:
    epoch_name: str
    probe_ids: tuple[str, ...]
    weights: tuple[int, ...]
    evidence_rule_ids: tuple[str, ...]
    implementation_digests: tuple[str, ...]
    baseline_state_id: str
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "omega.oeas.evaluator-epoch.v1"
    epoch_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.epoch_name, "epoch_name")
        object.__setattr__(
            self,
            "probe_ids",
            string_tuple(self.probe_ids, "probe_ids", identifiers=True),
        )
        if type(self.weights) is not tuple or any(
            type(value) is not int for value in self.weights
        ):
            raise TypeError("weights must be an exact integer tuple")
        if len(self.probe_ids) != len(self.weights) or not self.weights:
            raise ValueError("probe and weight arities must agree and be nonempty")
        if any(value <= 0 or value > 1_000_000 for value in self.weights):
            raise ValueError("evaluator weights must be positive bounded integers")
        object.__setattr__(
            self,
            "evidence_rule_ids",
            string_tuple(self.evidence_rule_ids, "evidence_rule_ids", identifiers=True),
        )
        object.__setattr__(
            self,
            "implementation_digests",
            string_tuple(
                self.implementation_digests,
                "implementation_digests",
                digests=True,
            ),
        )
        if not self.evidence_rule_ids or not self.implementation_digests:
            raise ValueError(
                "evaluator epoch requires evidence rules and implementations"
            )
        digest(self.baseline_state_id, "baseline_state_id")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("evaluator epoch authority_effect must be None")
        if self.schema_version != "omega.oeas.evaluator-epoch.v1":
            raise ValueError("unsupported evaluator epoch schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.epoch_id and self.epoch_id != expected:
            raise ValueError("epoch_id does not match canonical content")
        object.__setattr__(self, "epoch_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "epoch_name": self.epoch_name,
            "probe_ids": list(self.probe_ids),
            "weights": list(self.weights),
            "evidence_rule_ids": list(self.evidence_rule_ids),
            "implementation_digests": list(self.implementation_digests),
            "baseline_state_id": self.baseline_state_id,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "epoch_id": self.epoch_id}


@dataclass(frozen=True, slots=True)
class ValuationReceiptV1:
    evaluator_epoch_id: str
    candidate_id: str
    probe_ids: tuple[str, ...]
    weights: tuple[int, ...]
    pre_residual: tuple[int, ...]
    post_residual: tuple[int, ...]
    phi_pre: int
    phi_post: int
    delta_phi: int
    disposition: str
    independently_recomputed: bool
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "omega.oeas.valuation-receipt.v1"
    receipt_id: str = ""

    def __post_init__(self) -> None:
        digest(self.evaluator_epoch_id, "evaluator_epoch_id")
        digest(self.candidate_id, "candidate_id")
        object.__setattr__(
            self,
            "probe_ids",
            string_tuple(self.probe_ids, "probe_ids", identifiers=True),
        )
        for field in ("weights", "pre_residual", "post_residual"):
            values = getattr(self, field)
            if type(values) is not tuple or any(
                type(value) is not int for value in values
            ):
                raise TypeError(f"{field} must be an exact integer tuple")
            if any(value < 0 or value > 1_000_000 for value in values):
                raise ValueError(f"{field} contains an out-of-range value")
        if (
            not (
                len(self.probe_ids)
                == len(self.weights)
                == len(self.pre_residual)
                == len(self.post_residual)
            )
            or not self.probe_ids
        ):
            raise ValueError("valuation vector arities must agree and be nonempty")
        expected_pre = sum(
            weight * value
            for weight, value in zip(self.weights, self.pre_residual, strict=True)
        )
        expected_post = sum(
            weight * value
            for weight, value in zip(self.weights, self.post_residual, strict=True)
        )
        if self.phi_pre != expected_pre or self.phi_post != expected_post:
            raise ValueError(
                "Phi values are not derived from the frozen weighted residual"
            )
        if (
            type(self.delta_phi) is not int
            or self.delta_phi != self.phi_post - self.phi_pre
        ):
            raise ValueError("delta_phi is not derived")
        expected_disposition = "NON_INCREASING" if self.delta_phi <= 0 else "INCREASING"
        if self.disposition != expected_disposition:
            raise ValueError("valuation disposition is not derived")
        if (
            type(self.independently_recomputed) is not bool
            or not self.independently_recomputed
        ):
            raise ValueError("valuation must be independently recomputed")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("valuation receipt authority_effect must be None")
        if self.schema_version != "omega.oeas.valuation-receipt.v1":
            raise ValueError("unsupported valuation receipt schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.receipt_id and self.receipt_id != expected:
            raise ValueError("receipt_id does not match canonical content")
        object.__setattr__(self, "receipt_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "evaluator_epoch_id": self.evaluator_epoch_id,
            "candidate_id": self.candidate_id,
            "probe_ids": list(self.probe_ids),
            "weights": list(self.weights),
            "pre_residual": list(self.pre_residual),
            "post_residual": list(self.post_residual),
            "phi_pre": self.phi_pre,
            "phi_post": self.phi_post,
            "delta_phi": self.delta_phi,
            "disposition": self.disposition,
            "independently_recomputed": self.independently_recomputed,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "receipt_id": self.receipt_id}


@dataclass(frozen=True, slots=True)
class ProgressMeasureV1:
    changed_state: int = 0
    stronger_certificate: int = 0
    refined_residual: int = 0
    expanded_cover: int = 0
    proposed_lift: int = 0
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "omega.oeas.progress-measure.v1"
    measure_id: str = ""

    def __post_init__(self) -> None:
        for field in (
            "changed_state",
            "stronger_certificate",
            "refined_residual",
            "expanded_cover",
            "proposed_lift",
        ):
            integer(getattr(self, field), field, maximum=1_000_000)
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("progress measure authority_effect must be None")
        if self.schema_version != "omega.oeas.progress-measure.v1":
            raise ValueError("unsupported progress measure schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.measure_id and self.measure_id != expected:
            raise ValueError("measure_id does not match canonical content")
        object.__setattr__(self, "measure_id", expected)

    @property
    def progressed(self) -> bool:
        return any(
            getattr(self, field) > 0
            for field in (
                "changed_state",
                "stronger_certificate",
                "refined_residual",
                "expanded_cover",
                "proposed_lift",
            )
        )

    def _payload(self) -> dict[str, Any]:
        return {
            "changed_state": self.changed_state,
            "stronger_certificate": self.stronger_certificate,
            "refined_residual": self.refined_residual,
            "expanded_cover": self.expanded_cover,
            "proposed_lift": self.proposed_lift,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._payload(),
            "progressed": self.progressed,
            "measure_id": self.measure_id,
        }


@dataclass(frozen=True, slots=True)
class StopConditionV1:
    max_scene_steps: int
    max_dry_rounds: int
    max_total_budget: int
    stop_on_statuses: tuple[str, ...] = ("REFUSE",)

    def __post_init__(self) -> None:
        integer(self.max_scene_steps, "max_scene_steps", minimum=1)
        integer(self.max_dry_rounds, "max_dry_rounds", minimum=1)
        integer(self.max_total_budget, "max_total_budget", minimum=1)
        object.__setattr__(
            self,
            "stop_on_statuses",
            string_tuple(self.stop_on_statuses, "stop_on_statuses", identifiers=True),
        )
        if not self.stop_on_statuses:
            raise ValueError("stop condition requires terminal statuses")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_scene_steps": self.max_scene_steps,
            "max_dry_rounds": self.max_dry_rounds,
            "max_total_budget": self.max_total_budget,
            "stop_on_statuses": list(self.stop_on_statuses),
        }


__all__ = [
    "EvaluatorEpochV1",
    "ProgressMeasureV1",
    "StopConditionV1",
    "ValuationReceiptV1",
]
