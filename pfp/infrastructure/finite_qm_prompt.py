"""Reference prompt assembly over the existing shared task-turn implementation.

No provider, solver, stage machine, or budget ledger is duplicated here.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
import re
from hashlib import sha256
from importlib.resources import files

from pfp.domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
from pfp.infrastructure.task_turn import PreparedTaskTurn
from pfp.infrastructure.yaml_loading import strict_yaml_load
from pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase
from pfp.use_cases.pfp_proposal import task_turn_validator

ASSETS = "infrastructure/yaml/prompts/"
PROFILE = ASSETS + "finite_qm/"
SLOTS = (
    "slot_m1_layer0_ambient_carrier",
    "slot_m2_layer1_forward_morphisms",
    "slot_m3_layer2_ideals_and_annihilators",
    "slot_m4_tri_language_witness_anchors",
)
PRIVATE_KEYS = frozenset(
    {
        "ground_truth",
        "oracle_answer",
        "expected_answer",
        "solution",
        "expected_ground_truth",
        "host_diagnostics",
        "judge_diagnostics",
    }
)


def load_catalog() -> dict:
    return json.loads(
        files("pfp")
        .joinpath(ASSETS + "finite_qm_operad_catalog.json")
        .read_text(encoding="utf-8")
    )


def render_system_prompt(
    catalog: dict | None = None, *, selected_ids: tuple[str, ...] | None = None
) -> str:
    template = strict_yaml_load(
        files("pfp")
        .joinpath(PROFILE + "prompt_template.yaml")
        .read_text(encoding="utf-8")
    )
    system = template["system_prompt"].strip() + "\n"
    if selected_ids is None:
        return system
    catalog = load_catalog() if catalog is None else catalog
    entries = catalog["entries"]
    indexed = {entry["id"]: entry for entry in entries}
    if len(indexed) != len(entries):
        raise ValueError("DUPLICATE_CATALOG_ID")
    if (
        type(selected_ids) is not tuple
        or not selected_ids
        or len(set(selected_ids)) != len(selected_ids)
    ):
        raise ValueError("INVALID_CATALOG_SLICE")
    if not set(selected_ids) <= set(indexed):
        raise ValueError("UNKNOWN_CATALOG_ENTRY")
    lines = [system, "OPERATIONS SELECTED FOR THIS TASK"]
    for key in selected_ids:
        entry = indexed[key]
        if "inputs" not in entry:
            raise ValueError("REFERENCE_ONLY_CATALOG_ENTRY")
        lines.append(f"- {entry['name']}: ({', '.join(entry['inputs'])}) -> {entry['output']}.")
    return "\n".join(lines) + "\n"


def _public_exact(value):
    """Reject labelled judge data and lossy values, rather than silently filtering it."""
    if type(value) is dict:
        for key, item in value.items():
            if (
                type(key) is not str
                or key in PRIVATE_KEYS
                or key.startswith("expected_")
                or key.endswith("_expected")
            ):
                raise ValueError("PRIVATE_OR_INVALID_PUBLIC_FIELD")
            _public_exact(item)
    elif type(value) is list:
        for item in value:
            _public_exact(item)
    elif type(value) not in (str, int, bool, type(None)):
        raise ValueError("EXACT_PUBLIC_JSON_REQUIRED")


def _witness_schema(schema):
    """No answer instances/defaults or fixed numeric answers in public witness schemas.

    Free text still needs human leakage review. This is not a semantic secrecy proof.
    """
    if type(schema) is dict:
        if set(schema) & {"default", "examples", "example"}:
            raise ValueError("ANSWER_INSTANCE_IN_SCHEMA")
        if schema.get("type") == "number":
            raise ValueError("EXACT_WITNESS_SCHEMA_REQUIRED")
        for keyword in ("const", "enum"):
            if keyword in schema:
                values = schema[keyword] if keyword == "enum" else [schema[keyword]]
                if any(type(v) is not str and v is not None for v in values):
                    raise ValueError("ANSWER_VALUE_IN_SCHEMA")
        for key, item in schema.items():
            if key in (
                "properties",
                "$defs",
                "definitions",
                "patternProperties",
                "dependentSchemas",
            ):
                for child in item.values():
                    _witness_schema(child)
            elif key not in ("const", "enum"):
                _witness_schema(item)
    elif type(schema) is list:
        for item in schema:
            _witness_schema(item)


def prepare_finite_qm_turn(
    work_unit: dict,
    *,
    attempt_id: str,
    compact: bool = False,
    catalog: dict | None = None,
    stage_id: str = "P1_DERIVE",
    failure_codes: tuple[str, ...] = (),
):
    """Compile reviewed public M1..M4 slots to an existing PreparedTaskTurn.

    Populated slots are declarations. The caller supplies independent judges to
    turn.check(..., require_checker=True); compilation alone accepts no theorem.
    """
    if type(compact) is not bool:
        raise ValueError("INVALID_COMPACT_FLAG")
    if (
        type(work_unit) is not dict
        or set(work_unit)
        != {
            "schema_id",
            "task_id",
            "objective",
            "selected_catalog_ids",
            "operad_slots",
            "answer_schema",
            "checker_id",
        }
        or work_unit["schema_id"] != "core.pfp.finite-qm-work-unit.v1"
    ):
        raise ValueError("WORK_UNIT_SCHEMA")
    _public_exact(work_unit)
    for key in ("task_id", "objective", "checker_id"):
        if type(work_unit[key]) is not str or not work_unit[key].strip():
            raise ValueError("WORK_UNIT_IDENTITY")
    slots = work_unit["operad_slots"]
    if type(slots) is not dict or set(slots) != set(SLOTS):
        raise ValueError("FOUR_MISSIONS_REQUIRED")
    required = (
        {
            "mining_status",
            "carrier",
            "coefficient_ring",
            "assumptions",
            "source_pins",
            "public_input",
        },
        {"mining_status", "operations", "composition_plan"},
        {"mining_status", "algebraic_relations", "rejection_predicates", "negative_control_plan"},
        {"mining_status", "certificate_predicates", "anchors", "unpaid_imports"},
    )
    for name, keys in zip(SLOTS, required):
        slot = slots[name]
        if type(slot) is not dict or set(slot) != keys or slot.get("mining_status") != "FILLED":
            raise ValueError("UNFILLED_OR_INVALID_MISSION:" + name)
    m1, m2, m3, m4 = (slots[key] for key in SLOTS)
    for key in ("carrier", "coefficient_ring"):
        if type(m1[key]) is not str or not m1[key].strip():
            raise ValueError("CARRIER_REQUIRED")
    for slot, keys in (
        (m1, ("assumptions", "source_pins")),
        (m2, ("operations",)),
        (m3, ("algebraic_relations", "rejection_predicates")),
        (m4, ("certificate_predicates", "anchors", "unpaid_imports")),
    ):
        if any(type(slot[key]) is not list for key in keys):
            raise ValueError("MISSION_LIST_REQUIRED")
    if not m1["source_pins"] or not m2["operations"] or not m4["certificate_predicates"]:
        raise ValueError("SOURCE_OPERATION_AND_PREDICATES_REQUIRED")
    for pin in m1["source_pins"]:
        if type(pin) is not dict or set(pin) != {"path", "sha256"}:
            raise ValueError("SOURCE_PIN_SCHEMA")
        if (
            type(pin["path"]) is not str
            or not pin["path"]
            or type(pin["sha256"]) is not str
            or not re.fullmatch(r"[0-9a-f]{64}", pin["sha256"])
        ):
            raise ValueError("SOURCE_PIN_SCHEMA")
    catalog = load_catalog() if catalog is None else catalog
    selected = work_unit["selected_catalog_ids"]
    if (
        type(selected) is not list
        or not selected
        or any(type(s) is not str for s in selected)
        or len(set(selected)) != len(selected)
    ):
        raise ValueError("INVALID_CATALOG_SLICE")
    if not set(selected) <= {e["id"] for e in catalog["entries"]}:
        raise ValueError("UNKNOWN_CATALOG_ENTRY")
    for op in m2["operations"]:
        if type(op) is not dict or set(op) != {
            "catalog_id",
            "inputs",
            "output",
            "semantic_predicate",
        }:
            raise ValueError("OPERATION_SCHEMA")
        if (
            op["catalog_id"] not in selected
            or type(op["inputs"]) is not list
            or any(type(x) is not str for x in op["inputs"])
        ):
            raise ValueError("OPERATION_SLICE_BINDING")
        if any(
            type(op[key]) is not str or not op[key].strip()
            for key in ("output", "semantic_predicate")
        ):
            raise ValueError("OPERATION_SEMANTICS_REQUIRED")
        declared = next(e for e in catalog["entries"] if e["id"] == op["catalog_id"])
        if "inputs" not in declared:
            raise ValueError("REFERENCE_ONLY_CATALOG_ENTRY")
        if declared["inputs"] != op["inputs"] or declared["output"] != op["output"]:
            raise ValueError("CATALOG_SIGNATURE_MISMATCH")
    for value in (m2["composition_plan"], m3["negative_control_plan"]):
        if type(value) is not str or not value.strip():
            raise ValueError("PLAN_REQUIRED")
    if type(m1["public_input"]) is not dict:
        raise ValueError("PUBLIC_INPUT_REQUIRED")
    schema = work_unit["answer_schema"]
    if type(schema) is not dict:
        raise ValueError("ANSWER_SCHEMA_REQUIRED")
    _witness_schema(schema)
    task_turn_validator(schema)
    template = strict_yaml_load(
        files("pfp")
        .joinpath(PROFILE + "prompt_template.yaml")
        .read_text(encoding="utf-8")
    )
    workflow = strict_yaml_load(
        files("pfp").joinpath(PROFILE + "workflow.yaml").read_text(encoding="utf-8")
    )
    mode = strict_yaml_load(
        files("pfp").joinpath(PROFILE + "mode.yaml").read_text(encoding="utf-8")
    )
    if (
        template["workflow"] != "workflow.yaml"
        or template["mode"] != "mode.yaml"
        or workflow["mode"] != "mode.yaml"
    ):
        raise ValueError("PROFILE_ASSET_BINDING")
    stages = {stage["id"]: stage for stage in workflow["stages"]}
    if stage_id not in ("P1_DERIVE", "P3_REPAIR"):
        raise ValueError("STAGE_USES_A_DIFFERENT_CONTRACT")
    guidance = workflow["repair_guidance"]
    if type(failure_codes) is not tuple or any(
        type(code) is not str or code not in guidance for code in failure_codes
    ):
        raise ValueError("UNTRUSTED_REPAIR_FEEDBACK")
    if (stage_id == "P3_REPAIR") != bool(failure_codes):
        raise ValueError("REPAIR_STAGE_REQUIRES_FAILURE_CODES")
    instruction = stages[stage_id]["instruction"].strip()
    if failure_codes:
        instruction += "\nHost residual guidance:\n" + "\n".join(
            f"{code}: {guidance[code]}" for code in dict.fromkeys(failure_codes)
        )
    request = (
        template["user_prompt"]
        .replace("{{objective}}", work_unit["objective"])
        .replace("{{stage_instruction}}", instruction)
    )
    # compact is retained for existing callers; every rendering now selects the
    # task's operations and never appends the registry dump.
    system = render_system_prompt(catalog, selected_ids=tuple(selected))
    user = json.dumps(
        dict(
            instructions=request,
            operad_slots=slots,
            selected_catalog_ids=selected,
            mode_id=mode["mode_id"],
            run_limits=mode["bounds"],
            stage_id=stage_id,
        ),
        ensure_ascii=False,
        sort_keys=True,
    )
    # Bind the complete system rules without repeating the large catalog in the
    # public objective. Use the same task-turn use case and PreparedTaskTurn API.
    task = PfpTaskPrompt(
        work_unit["task_id"],
        work_unit["objective"],
        {
            "prompt": user,
            "context": {
                "profile": "finite-qm-task-turn-v1",
                "system_prompt_sha256": sha256(system.encode("utf-8")).hexdigest(),
            },
        },
        schema,
    )
    prompt = PreparePfpTaskTurnUseCase().execute(
        PfpPromptTemplate(system, "[USER PROMPT]", {}), task, attempt_id
    )
    return PreparedTaskTurn(task, prompt, work_unit["checker_id"])
