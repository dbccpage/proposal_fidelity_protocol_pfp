"""Shared basic P* and finite task contracts; no workflow selection."""

from __future__ import annotations

import json
from importlib.resources import files

import yaml

from pfp.domain.contracts.pfp_runtime import PfpPromptTemplate
from pfp.domain.pfp_ingress import strict_json
from pfp.use_cases.pfp_proposal import task_turn_validator

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
