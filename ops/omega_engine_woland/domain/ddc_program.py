"""Lightweight stored DDC procedure binding. AuthorityEffect: None."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator


class DdcProgramBinding(BaseModel):
    """A stored procedure's premises and prompt lineage, never a borrowed pass.

    ``family_id`` names the versioned prompt family, not the wire family or a
    containment edge. Stage and mode digests identify retained host artifacts;
    they do not attest that a model or checker executed them.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    schema_version: Literal["omega.woland.ddc-program.v1"] = "omega.woland.ddc-program.v1"
    family_id: StrictStr = Field(min_length=1, max_length=128)
    template_version: StrictStr = Field(min_length=1, max_length=128)
    storage_task_key: StrictStr = Field(min_length=1, max_length=128)
    prompt_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    premises_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    semantic_ddc_root: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    completed_stages: tuple[StrictInt, ...] = ()
    mode_ids: tuple[StrictInt, ...] = ()
    stage_artifacts_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    mode_artifacts_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    authority_effect: Literal["None"] = "None"

    @field_validator("family_id", "template_version", "storage_task_key")
    @classmethod
    def nonblank(cls, value):
        if not value.strip() or value != value.strip():
            raise ValueError("DDC_PROGRAM_ID_INVALID")
        return value

    @field_validator("completed_stages")
    @classmethod
    def stages(cls, value):
        if value != tuple(range(1, len(value) + 1)) or len(value) > 8:
            raise ValueError("DDC_STAGE_PREFIX_INVALID")
        return value

    @field_validator("mode_ids")
    @classmethod
    def modes(cls, value):
        if len(set(value)) != len(value) or any(not 1 <= v <= 20 for v in value):
            raise ValueError("DDC_MODE_IDS_INVALID")
        return value
