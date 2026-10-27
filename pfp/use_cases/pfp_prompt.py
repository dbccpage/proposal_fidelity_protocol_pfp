"""Answer-free PFP prompt assembly without filesystem or provider dependencies.

AuthorityEffect: None. Task-specific schemas are supplied by their owners.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from hashlib import sha256

from pfp.domain.contracts.pfp_runtime import (
    PfpPrompt,
    PfpPromptTemplate,
    PfpStagePromptInput,
    PfpTaskPrompt,
)

from .pfp_proposal import REPAIR_RULES, task_turn_validator

HIDDEN_KEYS = {
    "held_out_terms",
    "test_databases",
    "ground_truth",
    "optimal_cost",
    "solution",
    "category",
    "note",
    "oracle_answer",
    "host_diagnostics",
    "judge_diagnostics",
    "checker_diagnostics",
    "expected",
}
EXAMPLE_BLOCK = r"```(?:json)?\s*\n(.*?)```"


def stimulus(value):
    """Remove judge-only labels recursively without coercing or repairing input."""
    if type(value) is dict:
        return {
            k: stimulus(v)
            for k, v in value.items()
            if k not in HIDDEN_KEYS
            and not k.startswith("expected_")
            and not k.endswith("_expected")
        }
    if type(value) is list:
        return [stimulus(v) for v in value]
    return value


def task_contract(text: str) -> str:
    def schema(value):
        if type(value) is dict:
            return dict(
                type="object",
                properties={k: schema(v) for k, v in value.items()},
            )
        if type(value) is list:
            return dict(type="array", items=schema(value[0]) if value else {})
        return {
            "type": {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                type(None): "null",
            }[type(value)]
        }

    def redact(match):
        try:
            return (
                "\nWire field shape (values withheld):\n"
                + json.dumps(schema(json.loads(match[1])))
                + "\n"
            )
        except (ValueError, KeyError):
            return "\n[Example block withheld; follow the surrounding task contract.]\n"

    return re.sub(EXAMPLE_BLOCK, redact, text, flags=re.S)


def public_task_input(task: PfpTaskPrompt) -> dict:
    """Public task projection; oracle labels remain only in the host's original case."""
    public = dict(
        task_id=task.challenge,
        objective=task.task_text,
        input=stimulus(task.case),
        answer_schema=deepcopy(task.answer_schema),
    )

    # Validate native JSON input without converting tuples, objects or dictionary keys.
    def native(value):
        if type(value) is dict:
            if any(type(key) is not str for key in value):
                raise ValueError("INVALID_TASK_JSON_KEY")
            for item in value.values():
                native(item)
        elif type(value) is list:
            for item in value:
                native(item)
        elif type(value) not in (str, int, float, bool, type(None)):
            raise ValueError("INVALID_TASK_JSON_VALUE")

    native(public)
    json.dumps(public, allow_nan=False)
    return public


def task_input_sha256(task: PfpTaskPrompt) -> str:
    """Sorted ASCII JSON with compact separators; this is not an RFC 8785 claim."""
    return sha256(
        json.dumps(
            public_task_input(task),
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def task_turn_response_schema(task: PfpTaskPrompt, attempt_id: str) -> dict:
    if (
        type(task.challenge) is not str
        or not task.challenge.strip()
        or type(task.task_text) is not str
        or not task.task_text.strip()
        or type(attempt_id) is not str
        or not attempt_id.strip()
        or len(task.challenge) > 200
        or len(attempt_id) > 200
    ):
        raise ValueError("INVALID_TASK_OR_ATTEMPT_ID")
    if type(task.answer_schema) is not dict:
        raise ValueError("TASK_ANSWER_SCHEMA_REQUIRED")
    answer_schema = deepcopy(task.answer_schema)
    # Give the embedded answer its own resource root so local #/$defs references
    # keep their declared meaning after placing it inside the reply envelope.
    answer_schema.setdefault(
        "$id",
        "urn:pfp:answer:"
        + sha256(
            json.dumps(
                answer_schema,
                sort_keys=True,
                ensure_ascii=True,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
    )
    return dict(
        type="object",
        properties=dict(
            task_id=dict(type="string", const=task.challenge),
            attempt_id=dict(type="string", const=attempt_id),
            input_sha256=dict(type="string", const=task_input_sha256(task)),
            answer=answer_schema,
        ),
        required=["task_id", "attempt_id", "input_sha256", "answer"],
        additionalProperties=False,
    )


class PreparePfpTaskTurnUseCase:
    """One minimal typed task/role turn using the existing PFP prompt contracts."""

    def execute(
        self,
        template: PfpPromptTemplate,
        task: PfpTaskPrompt,
        attempt_id: str,
        *,
        feedback: str | None = None,
    ) -> PfpPrompt:
        if feedback is not None and (
            feedback not in REPAIR_RULES.values() or feedback == REPAIR_RULES["ENVELOPE"]
        ):
            raise ValueError("UNTRUSTED_REPAIR_FEEDBACK")
        # This profile binds the task's declared answer shape, without inheriting
        # SPK-only fields from a template intended for a different profile.
        schema = task_turn_response_schema(task, attempt_id)
        task_turn_validator(schema)
        public = public_task_input(task)
        public.update(
            attempt_id=attempt_id, input_sha256=schema["properties"]["input_sha256"]["const"]
        )
        user = json.dumps(public, sort_keys=True, ensure_ascii=False, allow_nan=False)
        if feedback is not None:
            user += "\nBounded host repair guidance: " + feedback
        return PfpPrompt(
            system=template.system
            + "\nYour answer is an untrusted proposal; schema validity is not task acceptance."
            + "\nReturn only a JSON instance that validates against this response schema."
            + " Do not return the schema itself, fences or extra text:\n"
            + json.dumps(schema, sort_keys=True, allow_nan=False),
            user=template.user.replace("[USER PROMPT]", user),
            response_schema=schema,
        )


class AssemblePfpPromptUseCase:
    def execute(
        self,
        template: PfpPromptTemplate,
        task: PfpTaskPrompt,
        arm: str = "baseline",
        feedback: str | None = None,
    ) -> PfpPrompt:
        if arm not in ("baseline", "typed_witness", "transfer"):
            raise ValueError("UNKNOWN_ARM")
        if feedback is not None and feedback not in REPAIR_RULES.values():
            raise ValueError("UNTRUSTED_REPAIR_FEEDBACK")
        response_schema = deepcopy(template.response_schema)
        response_schema["properties"]["answer"] = (
            deepcopy(task.answer_schema)
            if task.answer_schema is not None
            else {
                "type": "object",
                "description": "The original task's complete certificate; task-specific judges enforce its wire types.",
            }
        )
        response_schema["required"] = list(response_schema["properties"])
        literals = {}
        for block in re.findall(EXAMPLE_BLOCK, task.task_text, flags=re.S):
            try:
                example = json.loads(block)
            except ValueError:
                continue
            if type(example) is dict:
                for key in ("status", "kind", "verdict"):
                    if type(example.get(key)) is str:
                        literals.setdefault(key, set()).add(example[key])
        if "status" in literals:
            literals["status"].update(("SOLVED", "UNKNOWN", "OUT_OF_SCOPE"))
        if literals and task.answer_schema is None:
            response_schema["properties"]["answer"]["properties"] = {
                k: {"type": "string", "enum": sorted(v)} for k, v in literals.items()
            }
        seed = dict(
            challenge=task.challenge,
            task_contract=task_contract(task.task_text),
            input=stimulus(task.case),
        )
        rule = ""
        if arm in ("typed_witness", "transfer"):
            rule = (
                "Before submitting, privately check the task's exact wire types and all witness equations. "
                "Preserve identifiers. Use canonical exact rationals where required. A scalar claim without its witness is insufficient. "
                "Do not copy judge labels or invent a host acceptance. Keep the complete candidate in answer; leave sections empty."
            )
        if feedback is not None:
            rule += "\nPrevious stage host feedback: " + feedback
        user = json.dumps(seed, ensure_ascii=False, sort_keys=True) + "\n" + rule
        return PfpPrompt(
            system=template.system
            + "\nTask license: the mathematical operations explicitly defined in task_contract are licensed for this finite task only.\n"
            + "Return only this JSON response schema:\n"
            + json.dumps(response_schema),
            user=template.user.replace("[USER PROMPT]", user),
            response_schema=response_schema,
        )


class AssemblePfpStagePromptUseCase:
    """Assemble the existing numbered-stage templates from injected values."""

    def execute(self, source: PfpStagePromptInput) -> PfpPrompt:
        try:
            user = (
                source.user_format.format(**source.seed_data)
                if source.seed_data
                else source.user_format
            )
        except (KeyError, IndexError):
            if source.seed_data and "user_prompt" in source.seed_data:
                user = str(source.seed_data["user_prompt"])
            elif source.seed_data:
                user = "\n".join(f"{k}: {v}" for k, v in source.seed_data.items())
            else:
                user = source.user_format
        return PfpPrompt(source.system_format, user, deepcopy(source.response_schema))
