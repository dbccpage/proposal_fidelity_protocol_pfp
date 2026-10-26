"""Frozen operational Phi for the Woland engineering factory.

This is an engineering residual measure, not a cohomology claim.  Operators do
not import or call this module; the independent valuator does.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from omega_engine_woland.stage.domain import EvaluatorEpochV1, ValuationReceiptV1
from omega_engine_woland.stage.domain.canonical import (
    AUTHORITY_EFFECT_NONE,
    digest,
    integer,
    semantic_id,
    string_tuple,
)

WOLAND_ENGINEERING_PROBES = (
    "hard_truth_failures",
    "authority_failures",
    "anti_skill_failures",
    "test_failures",
    "unresolved_blocking_findings",
    "missing_acceptance_criteria",
    "replay_ownership_failures",
    "resource_overrun_units",
)


@dataclass(frozen=True, slots=True)
class WolandEngineeringResidualV1:
    hard_truth_failures: int
    authority_failures: int
    anti_skill_failures: int
    test_failures: int
    unresolved_blocking_findings: int
    missing_acceptance_criteria: int
    replay_ownership_failures: int
    resource_overrun_units: int

    def __post_init__(self) -> None:
        for field in WOLAND_ENGINEERING_PROBES:
            integer(getattr(self, field), field)

    @property
    def values(self) -> tuple[int, ...]:
        return tuple(getattr(self, field) for field in WOLAND_ENGINEERING_PROBES)

    def to_dict(self) -> dict[str, int]:
        return {field: getattr(self, field) for field in WOLAND_ENGINEERING_PROBES}


@dataclass(frozen=True, slots=True)
class WolandFactoryPhiV1:
    epoch: EvaluatorEpochV1

    def __post_init__(self) -> None:
        if type(self.epoch) is not EvaluatorEpochV1:
            raise TypeError("epoch must be exact EvaluatorEpochV1")
        if self.epoch.probe_ids != WOLAND_ENGINEERING_PROBES:
            raise ValueError("Woland evaluator does not bind the exact residual vector")

    def evaluate(
        self,
        *,
        candidate_id: str,
        pre: WolandEngineeringResidualV1,
        post: WolandEngineeringResidualV1,
    ) -> ValuationReceiptV1:
        if (
            type(pre) is not WolandEngineeringResidualV1
            or type(post) is not WolandEngineeringResidualV1
        ):
            raise TypeError("Woland residuals must be exact typed values")
        return ValuationReceiptV1(
            evaluator_epoch_id=self.epoch.epoch_id,
            candidate_id=candidate_id,
            probe_ids=self.epoch.probe_ids,
            weights=self.epoch.weights,
            pre_residual=pre.values,
            post_residual=post.values,
            phi_pre=sum(
                weight * value
                for weight, value in zip(self.epoch.weights, pre.values, strict=True)
            ),
            phi_post=sum(
                weight * value
                for weight, value in zip(self.epoch.weights, post.values, strict=True)
            ),
            delta_phi=sum(
                weight * (post_value - pre_value)
                for weight, pre_value, post_value in zip(
                    self.epoch.weights,
                    pre.values,
                    post.values,
                    strict=True,
                )
            ),
            disposition=(
                "NON_INCREASING"
                if sum(
                    weight * (post_value - pre_value)
                    for weight, pre_value, post_value in zip(
                        self.epoch.weights,
                        pre.values,
                        post.values,
                        strict=True,
                    )
                )
                <= 0
                else "INCREASING"
            ),
            independently_recomputed=True,
        )


def freeze_woland_evaluator_epoch_v1(
    *,
    epoch_name: str,
    weights: tuple[int, ...],
    evidence_rule_ids: tuple[str, ...],
    implementation_digests: tuple[str, ...],
    baseline_state_id: str,
) -> WolandFactoryPhiV1:
    if type(weights) is not tuple or len(weights) != len(WOLAND_ENGINEERING_PROBES):
        raise TypeError("Woland weights must match the exact residual arity")
    if any(type(weight) is not int or weight <= 0 for weight in weights):
        raise ValueError("Woland weights must be exact positive integers")
    return WolandFactoryPhiV1(
        EvaluatorEpochV1(
            epoch_name=epoch_name,
            probe_ids=WOLAND_ENGINEERING_PROBES,
            weights=weights,
            evidence_rule_ids=evidence_rule_ids,
            implementation_digests=implementation_digests,
            baseline_state_id=baseline_state_id,
        )
    )


@dataclass(frozen=True, slots=True)
class CohomologyImportBundleV1:
    finite_cover_refs: tuple[str, ...]
    overlap_refs: tuple[str, ...]
    coefficient_carrier_ref: str
    coboundary_implementation_digest: str
    residual_cochain_ref: str
    exactness_witness_ref: str
    owner_verification_receipt_ref: str
    homology_owner_implementation_digest: str
    higher_operad_owner_implementation_digest: str
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "omega.oeas.woland.cohomology-import-bundle.v1"
    bundle_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "finite_cover_refs",
            string_tuple(self.finite_cover_refs, "finite_cover_refs", digests=True),
        )
        object.__setattr__(
            self,
            "overlap_refs",
            string_tuple(self.overlap_refs, "overlap_refs", digests=True),
        )
        if not self.finite_cover_refs or not self.overlap_refs:
            raise ValueError("cohomology imports require a finite cover and overlaps")
        for field in (
            "coefficient_carrier_ref",
            "coboundary_implementation_digest",
            "residual_cochain_ref",
            "exactness_witness_ref",
            "owner_verification_receipt_ref",
            "homology_owner_implementation_digest",
            "higher_operad_owner_implementation_digest",
        ):
            digest(getattr(self, field), field)
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("cohomology import authority_effect must be None")
        if self.schema_version != "omega.oeas.woland.cohomology-import-bundle.v1":
            raise ValueError("unsupported cohomology import schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.bundle_id and self.bundle_id != expected:
            raise ValueError("bundle_id does not match canonical content")
        object.__setattr__(self, "bundle_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "finite_cover_refs": list(self.finite_cover_refs),
            "overlap_refs": list(self.overlap_refs),
            "coefficient_carrier_ref": self.coefficient_carrier_ref,
            "coboundary_implementation_digest": self.coboundary_implementation_digest,
            "residual_cochain_ref": self.residual_cochain_ref,
            "exactness_witness_ref": self.exactness_witness_ref,
            "owner_verification_receipt_ref": self.owner_verification_receipt_ref,
            "homology_owner_implementation_digest": self.homology_owner_implementation_digest,
            "higher_operad_owner_implementation_digest": self.higher_operad_owner_implementation_digest,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "bundle_id": self.bundle_id}


@dataclass(frozen=True, slots=True)
class CohomologyValuationReceiptV1:
    import_bundle: CohomologyImportBundleV1
    owner_valuation_receipt_ref: str
    status: str = "OWNER_RECEIPT_BOUND"
    nonclaims: tuple[str, ...] = (
        "The Woland operational Phi is not thereby a cohomology valuation.",
        "This wrapper binds but does not independently verify the owner receipt.",
    )
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "omega.oeas.woland.cohomology-valuation-receipt.v1"
    receipt_id: str = ""

    def __post_init__(self) -> None:
        if type(self.import_bundle) is not CohomologyImportBundleV1:
            raise TypeError("cohomology receipt requires an exact import bundle")
        digest(self.owner_valuation_receipt_ref, "owner_valuation_receipt_ref")
        if self.status != "OWNER_RECEIPT_BOUND":
            raise ValueError("cohomology status is not closed")
        object.__setattr__(self, "nonclaims", string_tuple(self.nonclaims, "nonclaims"))
        if not self.nonclaims:
            raise ValueError("cohomology receipt requires nonclaims")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("cohomology receipt authority_effect must be None")
        if self.schema_version != "omega.oeas.woland.cohomology-valuation-receipt.v1":
            raise ValueError("unsupported cohomology valuation schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.receipt_id and self.receipt_id != expected:
            raise ValueError("receipt_id does not match canonical content")
        object.__setattr__(self, "receipt_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "import_bundle": self.import_bundle.to_dict(),
            "owner_valuation_receipt_ref": self.owner_valuation_receipt_ref,
            "status": self.status,
            "nonclaims": list(self.nonclaims),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "receipt_id": self.receipt_id}


__all__ = [
    "WOLAND_ENGINEERING_PROBES",
    "CohomologyImportBundleV1",
    "CohomologyValuationReceiptV1",
    "WolandEngineeringResidualV1",
    "WolandFactoryPhiV1",
    "freeze_woland_evaluator_epoch_v1",
]
