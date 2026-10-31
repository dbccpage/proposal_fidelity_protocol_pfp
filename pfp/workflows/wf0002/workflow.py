"""WF2 prompt, typed candidate response and deterministic structural checks."""

import json
from copy import deepcopy
from hashlib import sha256
from importlib.resources import files

from pfp.domain.contracts.pfp_runtime import PfpPrompt, PfpTaskPrompt
from pfp.domain.pfp_ingress import strict_json
from pfp.infrastructure.task_turn import PreparedTaskTurn
from pfp.infrastructure.workflow_tasks import (
    BASE_TEMPLATE,
    basic_task_template,
    integer_sum_judge,
    validate_task_spec,
)
from pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase

from .collection import collect_emitted

WORKFLOW_ID = "WF2"
FOLDER = "wf0002"
VERSION = "0.2.0"
PACKAGE = "pfp.workflows.wf0002"
ATTEMPT_ID = "wf0002-stage-1"
SOURCE_FILES = tuple(
    "workflows/wf0002/" + name
    for name in (
        "workflow.py",
        "runner.py",
        "collection.py",
        "workflow.json",
        "slot_catalogue.json",
        "reference/ddc_alphabet.rs.txt",
        "answer.schema.json",
        "task_spec.schema.json",
    )
)
COLLECTION_FILES = ("collection.json",)


def resource_text(name):
    return files(PACKAGE).joinpath(name).read_text(encoding="utf-8")


def catalogue():
    return strict_json(resource_text("slot_catalogue.json"))


def validate_task(spec):
    return validate_task_spec(
        spec, strict_json(resource_text("task_spec.schema.json")), WORKFLOW_ID
    )


def response_schema(spec):
    schema = strict_json(resource_text("answer.schema.json"))
    result = deepcopy(spec["answer_schema"])
    result.setdefault(
        "$id",
        "urn:pfp:wf2:task-result:"
        + sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest(),
    )
    schema["properties"]["task_result"] = result
    return schema


def full_template():
    cat = catalogue()
    lines = [f"{row['id']}: {row['description']}" for row in cat["slots"]]
    instruction = (
        "WF2: solve the supplied task once. Its explicitly declared finite operations are licensed. "
        "Use task_result for the task's answer. Address every catalogue slot exactly once in slot_report. "
        "Use disposition provided with a concrete nonempty value, or not_applicable/unresolved with "
        "an empty value and a nonempty reason. Emit every operation you explicitly use or propose "
        "in operad_candidates, and every proposed DDC move in ddc_moves. Preserve order and duplicates; "
        "do not infer hidden reasoning or invent tool execution, citations or host receipts. "
        "Each operad's arity equals its ordered source_colours length. Its source quote must occur "
        "literally in seed_prompt or compact sorted JSON of input (input_json). Each DDC move has "
        "a local_log or refusal; operad_id is null or an emitted operad ID. Witness references name "
        "a catalogue slot, an emitted operad ID, or task_result. No pre-mining, swarm, rewriting or "
        "follow-up call occurs. All extracted material remains unverified candidate material. "
        "Do not add a legacy policy-stamp field to the four-field task-turn envelope.\n"
        "DDC: E exact repair; R residual projection; C context exposure; I integration; "
        "Λ (or Meta) structural lift; D descent; M mutation/typed refusal; T terminalization. "
        "Use canonical Λ in op. These are proposed trace records, not evidence of execution.\n"
        "Full pinned slot catalogue (" + cat["catalogue_id"] + "):\n" + "\n".join(lines)
    )
    return basic_task_template(instruction)


def prepare_task(spec):
    spec = validate_task(spec)
    task = PfpTaskPrompt(spec["task_id"], spec["seed_prompt"], spec["input"], response_schema(spec))
    prompt = PreparePfpTaskTurnUseCase().execute(full_template(), task, ATTEMPT_ID)
    # Compact serialization changes presentation only, retaining every schema
    # field and the original public task values and input digest.
    prefix, _ = prompt.system.rsplit("\n", 1)
    public = json.loads(prompt.user)
    # The full schema is already present in the system message. Keep one copy
    # rather than sending the same contract a second time as user data.
    public.pop("answer_schema")
    prompt = PfpPrompt(
        prefix + "\n" + json.dumps(prompt.response_schema, sort_keys=True, separators=(",", ":")),
        json.dumps(public, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
        prompt.response_schema,
    )
    return PreparedTaskTurn(task, prompt, spec["checker"])


def _sum_result(case, answer):
    return integer_sum_judge(case, answer["task_result"])


def judges_for(spec):
    return (("wf0002:integer_sum_v1", _sum_result),) if spec["checker"] == "integer_sum_v1" else ()


def source_texts(spec):
    return {
        "seed_prompt": spec["seed_prompt"],
        "input_json": json.dumps(
            spec["input"],
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ),
    }


def finalize_check(spec, checked):
    checked = deepcopy(checked)
    errors = []
    if not checked["schema_valid"]:
        checked.update(operad_structure_valid=False, structure_errors=["REPLY_SCHEMA_INVALID"])
        return checked
    answer = checked["answer"]
    slots = {row["id"] for row in catalogue()["slots"]}
    rows = answer["slot_report"]
    if len({row["slot"] for row in rows}) != len(rows) or {row["slot"] for row in rows} != slots:
        errors.append("SLOT_COVERAGE_OR_DUPLICATES")
    required = {"carrier", "equality_policy", "operands", "colours", "operators", "terminal"}
    for row in rows:
        if row["disposition"] == "provided":
            if not row["value"].strip():
                errors.append("EMPTY_PROVIDED_SLOT:" + row["slot"])
        elif row["value"] or not row["reason"].strip():
            errors.append("MISSING_SLOT_REASON:" + row["slot"])
        if row["slot"] in required and row["disposition"] != "provided":
            errors.append("REQUIRED_SLOT_UNRESOLVED:" + row["slot"])
    ops = answer["operad_candidates"]
    ids = [op["id"] for op in ops]
    if len(set(ids)) != len(ids):
        errors.append("DUPLICATE_OPERAD_ID")
    known = slots | set(ids) | {"task_result"}
    sources = source_texts(spec)
    for op in ops:
        if op["arity"] != len(op["source_colours"]):
            errors.append("ARITY_MISMATCH:" + op["id"])
        if op["source"]["quote"] not in sources[op["source"]["kind"]]:
            errors.append("SOURCE_QUOTE_MISSING:" + op["id"])
        if set(op["witness_refs"]) - known:
            errors.append("UNKNOWN_WITNESS_REF:" + op["id"])
    moves = answer["ddc_moves"]
    if len({move["id"] for move in moves}) != len(moves):
        errors.append("DUPLICATE_DDC_ID")
    for move in moves:
        if not any(
            type(move[key]) is str and move[key].strip() for key in ("local_log", "refusal")
        ):
            errors.append("DDC_LOG_OR_REFUSAL_REQUIRED:" + move["id"])
        if move["operad_id"] is not None and move["operad_id"] not in ids:
            errors.append("UNKNOWN_OPERAD_REF:" + move["id"])
        if set(move["witness_refs"]) - known:
            errors.append("UNKNOWN_WITNESS_REF:" + move["id"])
    checked.update(
        operad_structure_valid=not errors,
        structure_errors=errors,
        task_status=checked["status"],
        task_failure_class=checked["failure_class"],
    )
    if errors and checked["status"] != "CHECKER_DEFECT":
        checked.update(status="PROVIDER_COMPLETED", failure_class="WF2_OPERAD_STRUCTURE")
    return checked


def check_reply(spec, raw_reply):
    spec = validate_task(spec)
    checked = prepare_task(spec).check(
        raw_reply, judges=judges_for(spec), require_checker=spec["checker"] != "schema_only"
    )
    return finalize_check(spec, checked)


__all__ = ["BASE_TEMPLATE", "collect_emitted"]
