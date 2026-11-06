"""Shared basic P* and finite task contracts; no workflow selection."""

from __future__ import annotations

import json
import os
from importlib.resources import files

import yaml

from pfp.domain.contracts.pfp_runtime import PfpPromptTemplate
from pfp.domain.pfp_ingress import strict_json
from pfp.use_cases.pfp_proposal import task_turn_validator

REASONING_ENV = "PFP_REASONING"


def reasoning_policy() -> str | None:
    """Provider reasoning setting for workflow requests, from ``PFP_REASONING``.

    ``default`` (or unset) sends no reasoning field, as before. ``off`` asks
    OpenRouter to disable reasoning, so reasoning models do not spend the small
    fixed output allowances on hidden thinking. The choice is recorded in the
    retained wire request, so replay and audit can see it.
    """
    value = os.environ.get(REASONING_ENV, "default")
    if value == "default":
        return None
    if value == "off":
        return "disabled"
    raise ValueError("PFP_REASONING_MUST_BE_OFF_OR_DEFAULT")


BASE_TEMPLATE = "infrastructure/yaml/prompts/templates/template_standard_base.yaml"
SUM_ANSWER_SCHEMA = {
    "type": "object",
    "properties": {"total": {"type": "integer"}},
    "required": ["total"],
    "additionalProperties": False,
}


def validate_task_spec(spec: dict, schema, workflow_id) -> dict:
    """Validate native JSON types; no stages, agents or extensions are configurable."""

    def native(value):
        if type(value) is dict:
            if any((type(key) is not str for key in value)):
                raise ValueError(f"{workflow_id}_NATIVE_JSON_REQUIRED")
            for item in value.values():
                native(item)
        elif type(value) is list:
            for item in value:
                native(item)
        elif type(value) not in (str, int, float, bool, type(None)):
            raise ValueError(f"{workflow_id}_NATIVE_JSON_REQUIRED")

    native(spec)
    spec = strict_json(json.dumps(spec, ensure_ascii=False, allow_nan=False))
    validator = task_turn_validator(schema)
    if not validator.is_valid(spec):
        raise ValueError(f"{workflow_id}_INVALID_TASK_SPECIFICATION")
    if spec["checker"] == "integer_sum_v1":
        values = spec["input"].get("values")
        if (
            set(spec["input"]) != {"values"}
            or type(values) is not list
            or (not 1 <= len(values) <= 1024)
            or any((type(value) is not int or abs(value) > 10**100 for value in values))
            or (spec["answer_schema"] != SUM_ANSWER_SCHEMA)
        ):
            raise ValueError(f"{workflow_id}_INTEGER_SUM_CONTRACT")
    return spec


def basic_task_template(instruction) -> PfpPromptTemplate:
    """Reuse the canonical base manifest with the shared task-turn answer schema."""
    source = yaml.safe_load(
        files("pfp").joinpath(BASE_TEMPLATE).read_text(encoding="utf-8")
    )
    system = yaml.safe_dump(source["system_prompt"], sort_keys=False, allow_unicode=True)
    system += "\n" + instruction
    return PfpPromptTemplate(system, "[USER PROMPT]", {})


def integer_sum_judge(case: dict, answer: object) -> tuple[bool, str]:
    """Check the declared finite integer task, without a model or stored answer."""
    accepted = (
        type(answer) is dict
        and set(answer) == {"total"}
        and (type(answer["total"]) is int)
        and (answer["total"] == sum(case["values"]))
    )
    return (accepted, "Exact integer sum agrees." if accepted else "Incorrect integer sum.")
