"""WF1-only task contract, composed from shared PFP components."""

from importlib.resources import files

from pfp.domain.contracts.pfp_runtime import PfpTaskPrompt
from pfp.domain.pfp_ingress import strict_json
from pfp.infrastructure.task_turn import PreparedTaskTurn
from pfp.infrastructure.workflow_tasks import (
    BASE_TEMPLATE,
    basic_task_template,
    integer_sum_judge,
    validate_task_spec,
)
from pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase

WORKFLOW_ID = "WF1"
FOLDER = "wf0001"
VERSION = "0.2.0"
PACKAGE = "pfp.workflows.wf0001"
ATTEMPT_ID = "wf0001-stage-1"
SOURCE_FILES = tuple(
    "workflows/wf0001/" + name
    for name in ("workflow.py", "runner.py", "workflow.json", "task_spec.schema.json")
)
COLLECTION_FILES = ()
__all__ = ["BASE_TEMPLATE"]


def resource_text(name: str) -> str:
    return files(PACKAGE).joinpath(name).read_text(encoding="utf-8")


def validate_task(spec: dict) -> dict:
    return validate_task_spec(
        spec, strict_json(resource_text("task_spec.schema.json")), WORKFLOW_ID
    )


def basic_template():
    return basic_task_template(
        "WF1: complete only the supplied task in one response. "
        "The task's explicitly declared finite operations are licensed for this task. "
        "Return the task-turn JSON contract attached by the host. "
        "No operad extraction, pre-mining, seed rewriting or additional agent is requested."
    )


def prepare_task(spec: dict) -> PreparedTaskTurn:
    spec = validate_task(spec)
    task = PfpTaskPrompt(spec["task_id"], spec["seed_prompt"], spec["input"], spec["answer_schema"])
    prompt = PreparePfpTaskTurnUseCase().execute(basic_template(), task, ATTEMPT_ID)
    return PreparedTaskTurn(task, prompt, spec["checker"])


def judges_for(spec: dict) -> tuple:
    return (
        (("wf0001:integer_sum_v1", integer_sum_judge),)
        if spec["checker"] == "integer_sum_v1"
        else ()
    )


def check_reply(spec: dict, raw_reply: bytes) -> dict:
    spec = validate_task(spec)
    return prepare_task(spec).check(
        raw_reply, judges=judges_for(spec), require_checker=spec["checker"] != "schema_only"
    )
