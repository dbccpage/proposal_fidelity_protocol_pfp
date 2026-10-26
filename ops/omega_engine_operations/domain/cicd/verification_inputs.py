"""Independent values supplied by the host adapter during verification."""

from __future__ import annotations

from pydantic import field_validator

from omega_engine_operations.domain.cicd.anchors import (
    TrustedEvaluatorAnchorV1,
    _validate_anchors,
)
from omega_engine_operations.domain.cicd.base import _AuthorityNullModel
from omega_engine_operations.domain.cicd.fields import GitOid, Sha256
from omega_engine_operations.domain.cicd.manifest import (
    CanonicalCandidateManifestV1,
)


class LocalCiVerificationInputsV1(_AuthorityNullModel):
    """Independent values supplied by the host adapter during verification."""

    observed_head_before: GitOid
    observed_head_after: GitOid
    observed_main_before: GitOid
    observed_main_after: GitOid
    expected_results_sha256: Sha256
    candidate_manifest: CanonicalCandidateManifestV1
    evaluator_anchors: tuple[TrustedEvaluatorAnchorV1, ...]

    @field_validator("evaluator_anchors")
    @classmethod
    def _validate_evaluator_anchors(
        cls, value: tuple[TrustedEvaluatorAnchorV1, ...]
    ) -> tuple[TrustedEvaluatorAnchorV1, ...]:
        return _validate_anchors(value)
