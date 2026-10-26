"""Local CI execution invocation aggregate."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from omega_engine_operations.domain.cicd.anchors import (
    TrustedEvaluatorAnchorV1,
    _validate_anchors,
)
from omega_engine_operations.domain.cicd.base import _AuthorityNullModel
from omega_engine_operations.domain.cicd.constants import _INVOCATION_SCHEMA
from omega_engine_operations.domain.cicd.fields import GitOid, Sha256
from omega_engine_operations.domain.cicd.manifest import (
    CanonicalCandidateManifestV1,
)


class LocalCiInvocationV1(_AuthorityNullModel):
    """Execution input specification for local CI."""

    schema_id: Literal["omega.local_ci.invocation.v1"] = Field(
        default=_INVOCATION_SCHEMA, alias="schema"
    )
    expected_head: GitOid
    observed_head_before: GitOid
    expected_main: GitOid
    observed_main_before: GitOid
    nonce: Sha256
    gate_catalog_sha256: Sha256
    candidate_manifest: CanonicalCandidateManifestV1
    evaluator_anchors: tuple[TrustedEvaluatorAnchorV1, ...]

    @field_validator("evaluator_anchors")
    @classmethod
    def _validate_evaluator_anchors(
        cls, value: tuple[TrustedEvaluatorAnchorV1, ...]
    ) -> tuple[TrustedEvaluatorAnchorV1, ...]:
        return _validate_anchors(value)
