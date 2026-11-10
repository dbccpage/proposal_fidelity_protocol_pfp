"""PFP prompt and bounded-stage contracts. AuthorityEffect: None."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class PfpPromptTemplate:
    system: str
    user: str
    response_schema: dict[str, Any]

    def __post_init__(self):
        if not self.system or "[USER PROMPT]" not in self.user:
            raise ValueError("INVALID_PFP_TEMPLATE")


@dataclass(frozen=True)
class PfpTaskPrompt:
    challenge: str
    task_text: str
    case: dict[str, Any]
    answer_schema: dict[str, Any] | None = None

    def __post_init__(self):
        if not self.challenge or not self.task_text or type(self.case) is not dict:
            raise ValueError("INVALID_PFP_TASK")


@dataclass(frozen=True)
class PfpPrompt:
    system: str
    user: str
    response_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(system=self.system, user=self.user, response_schema=self.response_schema)


@dataclass(frozen=True)
class PfpPreparedStage:
    payload: object
    wire_body: dict[str, Any]
    reserved_microusd: int

    def __post_init__(self):
        if type(self.reserved_microusd) is not int or not 0 <= self.reserved_microusd <= 50000:
            raise ValueError("RUN_CAP_EXCEEDED")


@dataclass(frozen=True)
class PfpStageReceipt:
    data: dict[str, Any]

    def __post_init__(self):
        if type(self.data.get("cost_microusd")) is not int or self.data["cost_microusd"] < 0:
            raise ValueError("INVALID_COST")
        if type(self.data.get("generation_id")) is not str or not self.data["generation_id"]:
            raise ValueError("PROVIDER_IDENTITY_MISMATCH")
        result = self.data["result"]
        if (
            result["status"]
            not in {
                "HOST_ACCEPTED",
                "TYPED_REFUSAL",
                "PROVIDER_COMPLETED",
                "CHECKER_DEFECT",
                "INFRASTRUCTURE_ERROR",
            }
            or type(result["failure_class"]) is not str
        ):
            raise ValueError("INVALID_STAGE_RESULT")


class PfpStagePort(Protocol):
    """Injected I/O; the use case owns dispatch order and continuation decisions."""

    def assemble(self, feedback: str | None) -> PfpPrompt: ...
    def prepare(self, prompt: PfpPrompt) -> PfpPreparedStage: ...
    def reserve(self, stage: int, amount: int) -> None: ...
    def record_request(self, stage: int, prepared: PfpPreparedStage) -> None: ...
    def dispatch(self, prepared: PfpPreparedStage) -> bytes: ...
    def record_raw(self, stage: int, raw: bytes) -> None: ...
    def grade(self, raw: bytes) -> PfpStageReceipt: ...
    def record_receipt(self, stage: int, receipt: PfpStageReceipt, elapsed: float) -> None: ...
    def settle(self, stage: int, receipt: PfpStageReceipt, reserve: int) -> None: ...
    def record_failure(self, stage: int, failure: dict[str, Any]) -> None: ...
    def summarize(self, summary: dict[str, Any]) -> None: ...
    def observe(self, stage: int, receipt: PfpStageReceipt) -> None: ...


@dataclass(frozen=True)
class PfpStagePromptInput:
    system_format: str
    user_format: str
    seed_data: dict[str, Any]
    response_schema: dict[str, Any]

    def __post_init__(self):
        if type(self.system_format) is not str or type(self.user_format) is not str:
            raise ValueError("INVALID_STAGE_TEMPLATE")
        if type(self.seed_data) is not dict or type(self.response_schema) is not dict:
            raise ValueError("INVALID_STAGE_PROMPT_INPUT")


@dataclass(frozen=True)
class PfpPipelineStep:
    data: dict[str, Any]
    should_continue: bool

    def __post_init__(self):
        if type(self.data) is not dict or type(self.should_continue) is not bool:
            raise ValueError("INVALID_PIPELINE_STEP")


@dataclass(frozen=True)
class PfpPipelineRun:
    completed_stages: tuple[int, ...]
    stage_responses: dict[int, dict[str, Any]]
    all_stages_passed: bool
    terminal_status: str
    operad_execution: dict[str, Any] | None = None


class PfpPipelineFailure(ValueError):
    def __init__(self, code: str, message: str, stage: int | None = None):
        super().__init__(message)
        self.code, self.stage = code, stage


class PfpPipelinePort(Protocol):
    """Validated model stages and the host stages (1, 5, 7, 8, 9, 10), each run by the host."""

    def execute_model_stage(
        self, stage: int, prior_responses: dict[int, dict[str, Any]]
    ) -> PfpPipelineStep: ...
    def execute_host_stage(
        self, stage: int, prior_responses: dict[int, dict[str, Any]]
    ) -> PfpPipelineStep: ...


class PfpPipelineRunnerPort(Protocol):
    """Optional composition runner injected at the outer application boundary."""

    def execute(self, stages: tuple[int, ...], port: PfpPipelinePort, *,
                demo_id: str, original_seed: dict[str, Any]) -> PfpPipelineRun: ...
