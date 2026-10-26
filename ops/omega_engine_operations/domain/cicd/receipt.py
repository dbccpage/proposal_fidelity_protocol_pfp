"""Local CI execution receipt aggregate root."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from omega_engine_operations.domain.cicd.anchors import (
    TrustedEvaluatorAnchorV1,
    _validate_anchors,
)
from omega_engine_operations.domain.cicd.base import _AuthorityNullModel
from omega_engine_operations.domain.cicd.constants import _RECEIPT_SCHEMA
from omega_engine_operations.domain.cicd.enums import LocalCiVerdict
from omega_engine_operations.domain.cicd.fields import GitOid, Sha256
from omega_engine_operations.domain.cicd.manifest import (
    CanonicalCandidateManifestV1,
)
from omega_engine_operations.domain.cicd.result import (
    AdvisoryFindingV1,
    GateResult,
    QuarantineResidualV1,
)


class LocalCiExecutionReceiptV3(_AuthorityNullModel):
    """Immutable, authority-null execution receipt for a completed local-CI run."""

    schema_id: Literal["omega.local_ci.execution_receipt.v3"] = Field(
        default=_RECEIPT_SCHEMA, alias="schema"
    )
    expected_head: GitOid
    observed_head_before: GitOid
    observed_head_after: GitOid
    expected_main: GitOid
    observed_main_before: GitOid
    observed_main_after: GitOid
    nonce: Sha256
    gate_catalog_sha256: Sha256
    candidate_manifest: CanonicalCandidateManifestV1
    evaluator_anchors: tuple[TrustedEvaluatorAnchorV1, ...]
    results: tuple[GateResult, ...]
    results_sha256: Sha256
    quarantine_residuals: tuple[QuarantineResidualV1, ...]
    advisory_findings: tuple[AdvisoryFindingV1, ...]
    verdict: LocalCiVerdict

    @field_validator("evaluator_anchors")
    @classmethod
    def _validate_evaluator_anchors(
        cls, value: tuple[TrustedEvaluatorAnchorV1, ...]
    ) -> tuple[TrustedEvaluatorAnchorV1, ...]:
        return _validate_anchors(value)
