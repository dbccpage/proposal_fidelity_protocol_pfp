"""Candidate manifest aggregate models and entries."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from omega_engine_operations.domain.cicd.base import (
    _AuthorityNullModel,
    _StrictFrozenModel,
)
from omega_engine_operations.domain.cicd.constants import _MANIFEST_SCHEMA
from omega_engine_operations.domain.cicd.fields import (
    CandidatePath,
    GitOid,
    OptionalBlobOid,
    OptionalSha256,
)
from omega_engine_operations.domain.cicd.validators import _sorted_unique


class CandidateManifestEntryV1(_StrictFrozenModel):
    """Candidate file entry recorded in a candidate manifest."""

    path: CandidatePath
    blob_oid: OptionalBlobOid
    content_sha256: OptionalSha256

    @model_validator(mode="after")
    def _validate_presence_pair(self) -> CandidateManifestEntryV1:
        if (self.blob_oid is None) != (self.content_sha256 is None):
            raise ValueError("blob_oid and content_sha256 must both be present or null")
        return self


class CanonicalCandidateManifestV1(_AuthorityNullModel):
    """Canonical, sorted, collision-free candidate manifest."""

    schema_id: Literal["omega.local_ci.candidate_manifest.v1"] = Field(
        default=_MANIFEST_SCHEMA, alias="schema"
    )
    base_oid: GitOid
    head_oid: GitOid
    entries: tuple[CandidateManifestEntryV1, ...]

    @field_validator("entries")
    @classmethod
    def _validate_entries(
        cls, value: tuple[CandidateManifestEntryV1, ...]
    ) -> tuple[CandidateManifestEntryV1, ...]:
        paths = tuple(entry.path for entry in value)
        _sorted_unique(paths, field="candidate manifest paths", casefold_unique=True)
        return value


CandidateManifestV1 = CanonicalCandidateManifestV1
