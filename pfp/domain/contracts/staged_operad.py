"""Refined JSON carriers for the canonical staged planar pipeline (any runnable subset).

Native OEWAS checks the ordered StageFrame ports. These Python contracts refine
the JSON carried by those ports; they are not native semantic proofs. A frame
names the requested stage subset and how many of its stages have run; frame
colour k is the state after the k-th requested stage, whatever its number.
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator

CONTROLLER_VERSION = "pfp-staged.0.3"
FRAME_PROFILE = "pfp.stage-subset-frame.v1"
MAX_STAGE = 11


def json_digest(value: Any) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


class StageResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    stage: StrictInt = Field(ge=1, le=MAX_STAGE)
    data: dict[str, Any]
    controller_continue: StrictBool


class StageFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    profile: Literal["pfp.stage-subset-frame.v1"] = FRAME_PROFILE
    controller_version: Literal["pfp-staged.0.3"] = CONTROLLER_VERSION
    stages: tuple[StrictInt, ...] = Field(min_length=1, max_length=MAX_STAGE)
    completed_count: StrictInt = Field(ge=0, le=MAX_STAGE)
    demo_id: StrictStr = Field(min_length=1)
    original_seed: dict[str, Any]
    original_seed_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    prior_results: tuple[StageResult, ...] = ()
    continue_pipeline: StrictBool = True
    terminal_status: StrictStr | None = None

    @model_validator(mode="before")
    @classmethod
    def strict_frame_index(cls, value):
        if isinstance(value, dict) and "completed_count" in value and type(value["completed_count"]) is not int:
            raise ValueError("PFP_STAGE_SUBSET_MISMATCH")
        return value

    @model_validator(mode="after")
    def subset_and_source(self):
        if json_digest(self.original_seed) != self.original_seed_sha256:
            raise ValueError("PFP_STAGE_SEED_CHANGED")
        if (self.stages[0] != 1 or any(not 1 <= s <= MAX_STAGE for s in self.stages)
                or any(a >= b for a, b in zip(self.stages, self.stages[1:]))):
            raise ValueError("PFP_STAGE_SUBSET_INVALID")
        if (self.completed_count > len(self.stages) or len(self.prior_results) != self.completed_count
                or tuple(item.stage for item in self.prior_results) != self.stages[:self.completed_count]):
            raise ValueError("PFP_STAGE_SUBSET_MISMATCH")
        for item in self.prior_results:
            json_digest(item.data)
            if (type(item.data.get("stage")) is not int or item.data["stage"] != item.stage
                    or item.data.get("demo_id") != self.demo_id or item.data.get("authority_effect") != "None"):
                raise ValueError("PFP_STAGE_RESULT_BINDING_MISMATCH")
        if self.continue_pipeline == (self.terminal_status is not None):
            raise ValueError("PFP_STAGE_TERMINAL_MISMATCH")
        done = self.completed_by_stage
        if 2 in done:
            candidates = done[2].get("candidates")
            if (type(candidates) is not list or not candidates
                    or any(type(item) is not dict or type(item.get("candidate_id")) is not str
                           or not item["candidate_id"] for item in candidates)):
                raise ValueError("PFP_STAGE2_CANDIDATES_REQUIRED")
            ids = [item["candidate_id"] for item in candidates]
            if len(ids) != len(set(ids)):
                raise ValueError("PFP_STAGE2_CANDIDATE_ID_DUPLICATED")
        if 4 in done:
            selected = done[4]
            if (type(selected.get("candidate")) is not dict
                    or selected.get("candidate_id") not in {item["candidate_id"] for item in self.stage2_candidates}):
                raise ValueError("PFP_STAGE4_CANDIDATE_BINDING_MISMATCH")
        if 5 in done:
            host = done[5]
            if type(host.get("host_verdict")) is not str or type(host.get("exact_checks_passed")) is not bool:
                raise ValueError("PFP_STAGE5_HOST_EVIDENCE_REQUIRED")
        return self

    @property
    def completed_by_stage(self) -> dict[int, dict[str, Any]]:
        return {item.stage: item.data for item in self.prior_results}

    @property
    def last_stage(self) -> int | None:
        return self.prior_results[-1].stage if self.prior_results else None

    @property
    def stage2_candidates(self) -> list[dict[str, Any]]:
        return self.completed_by_stage.get(2, {}).get("candidates", [])

    @property
    def stage4_candidate(self) -> dict[str, Any] | None:
        stage4 = self.completed_by_stage.get(4)
        return None if stage4 is None else stage4["candidate"]

    @property
    def stage5_host_evidence(self) -> dict[str, Any] | None:
        return self.completed_by_stage.get(5)


class StageFrame0(StageFrame):
    completed_count: Literal[0] = 0


class StageFrame1(StageFrame):
    completed_count: Literal[1] = 1


class StageFrame2(StageFrame):
    completed_count: Literal[2] = 2


class StageFrame3(StageFrame):
    completed_count: Literal[3] = 3


class StageFrame4(StageFrame):
    completed_count: Literal[4] = 4


class StageFrame5(StageFrame):
    completed_count: Literal[5] = 5


class StageFrame6(StageFrame):
    completed_count: Literal[6] = 6


class StageFrame7(StageFrame):
    completed_count: Literal[7] = 7


class StageFrame8(StageFrame):
    completed_count: Literal[8] = 8


class StageFrame9(StageFrame):
    completed_count: Literal[9] = 9


class StageFrame10(StageFrame):
    completed_count: Literal[10] = 10


class StageFrame11(StageFrame):
    completed_count: Literal[11] = 11


FRAME_TYPES = (
    StageFrame0,
    StageFrame1,
    StageFrame2,
    StageFrame3,
    StageFrame4,
    StageFrame5,
    StageFrame6,
    StageFrame7,
    StageFrame8,
    StageFrame9,
    StageFrame10,
    StageFrame11,
)
