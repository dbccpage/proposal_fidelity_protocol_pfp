"""Evaluator anchor value objects and collection validator."""

from __future__ import annotations

from operations.domain.cicd.base import _StrictFrozenModel
from operations.domain.cicd.fields import (
    AnchorName,
    AnchorPath,
    BlobOid,
    Sha256,
)
from operations.domain.cicd.validators import _sorted_unique


class TrustedEvaluatorAnchorV1(_StrictFrozenModel):
    """Integrity binding to a trusted evaluator module."""

    name: AnchorName
    path: AnchorPath
    blob_oid: BlobOid
    content_sha256: Sha256


EvaluatorAnchorV1 = TrustedEvaluatorAnchorV1


def _validate_anchors(
    anchors: tuple[TrustedEvaluatorAnchorV1, ...],
) -> tuple[TrustedEvaluatorAnchorV1, ...]:
    """Validate that evaluator anchors collection is non-empty, sorted, and unique."""
    if not anchors:
        raise ValueError("evaluator_anchors must not be empty")
    names = tuple(anchor.name for anchor in anchors)
    _sorted_unique(names, field="evaluator anchor names", casefold_unique=True)
    return anchors
