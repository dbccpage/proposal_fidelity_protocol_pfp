"""WF3 contracts; WF2's pinned pure codec is reused, never its runtime or state."""

import json
import re
from copy import deepcopy
from importlib.resources import files

import yaml

from pfp.domain.contracts.pfp_runtime import (
    PfpPrompt,
    PfpPromptTemplate,
    PfpTaskPrompt,
)
from pfp.domain.pfp_ingress import strict_json
from pfp.infrastructure.adapters.pfp_campaign import canonical, digest
from pfp.infrastructure.task_turn import PreparedTaskTurn
from pfp.infrastructure.workflow_tasks import (
    BASE_TEMPLATE,
    basic_task_template,
    integer_sum_judge,
    validate_task_spec,
)
from pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase, stimulus
from pfp.workflows.wf0002 import workflow as operad_codec

from . import structured

PACKAGE = "pfp.workflows.wf0003"
VERSION = "0.4.0"
CORE_REQUIRED = {"carrier", "equality_policy", "operands", "colours", "operators", "terminal"}
SUM_L2 = {
    "concrete_spans",
    "parameter_bindings",
    "instantiated_arguments",
    "preservation_obligations",
}
COMMON_SOURCES = tuple(
    "workflows/wf0003/" + name
    for name in (
        "workflow.py",
        "runner.py",
        "workflow.json",
        "mining_answer.schema.json",
        "task_spec.schema.json",
        "structured.py",
    )
)
UPSTREAM_SOURCES = tuple(
    path for path in operad_codec.SOURCE_FILES if not path.endswith("runner.py")
)


def resource_text(name):
    return files(PACKAGE).joinpath(name).read_text(encoding="utf-8")


def validate_task(spec):
    spec = validate_task_spec(spec, strict_json(resource_text("task_spec.schema.json")), "WF3")
    if "pfp_mined_attachment" in spec["input"]:
        raise ValueError("WF3_RESERVED_ATTACHMENT_KEY")
    return spec


def required_slots(spec):
    return CORE_REQUIRED | (SUM_L2 if spec["checker"] == "integer_sum_v1" else set())


def solver_response_schema(spec, operations):
    return structured.answer_schema(spec, required_slots(spec), operations)


class MiningContract:
    WORKFLOW_ID = "WF3_MINER"
    FOLDER = "wf0003"
    VERSION = VERSION
    BASE_TEMPLATE = BASE_TEMPLATE
    ATTEMPT_ID = "wf0003-mining-1"
    SOURCE_FILES = COMMON_SOURCES + UPSTREAM_SOURCES
    COLLECTION_FILES = ()

    @staticmethod
    def validate_task(spec):
        spec = validate_task(spec)
        spec["checker"] = "schema_only"
        return spec

    @staticmethod
    def prepare_task(spec):
        spec = MiningContract.validate_task(spec)
        schema = strict_json(resource_text("mining_answer.schema.json"))
        instruction = (
            "Pre-mine a small set of reusable typed operations for the supplied seed. Do not solve it. "
            "Return structural guidance only, no numerical results, computed intermediate values, "
            "answers, examples containing answers, citations or execution claims. Free-text fields "
            "must contain no decimal digits; arity and literal source quotes are the only exceptions. "
            "Use literal source quote substrings from seed_prompt. "
            "Witness refs name catalogue slots or task_result. Choose up to two concise operations, "
            "a few focus_slots and concrete failure_triggers. All outputs are unverified candidates."
            " Count typed input PORTS, not data elements: an operation on one IntegerList has "
            "source_colours [IntegerList] and arity one, regardless of how many numbers it contains. "
            "Make arity equal the number of entries in source_colours. Use letter/underscore-only "
            "IDs such as sum, without numbered suffixes. For this run quote only seed_prompt, "
            "copying a literal substring exactly; do not invent a source key. Prefer one grounded operation. "
            "Return exactly FOUR distinct l2_guidance records, one each for concrete_spans, "
            "parameter_bindings, instantiated_arguments and preservation_obligations, grounded in "
            "literal seed_prompt or compact sorted input_json quotes. Do not return only focus slots. "
            "Each guidance is one short imperative sentence, at most eighty characters. "
            "For integer lists cover concrete_spans, parameter_bindings, instantiated_arguments and "
            "preservation_obligations: locate input.values, bind its signed integers to one IntegerList "
            "port, and require every operand exactly once with exact integer arithmetic and no rounding. "
            "Do not calculate a total or an intermediate result. Do not invent boundary conditions or proofs."
        )
        task = PfpTaskPrompt(
            spec["task_id"],
            "Pre-mine typed operations and source-grounded L2 guidance. Do not solve the seed.",
            {"seed_prompt": spec["seed_prompt"], "input": stimulus(spec["input"])},
            schema,
        )
        prompt = PreparePfpTaskTurnUseCase().execute(
            PfpPromptTemplate(instruction, "[USER PROMPT]", {}), task, MiningContract.ATTEMPT_ID
        )
        # The exact full schema is already in the system message.
        public = json.loads(prompt.user)
        public.pop("answer_schema")
        prefix, _ = prompt.system.rsplit("\n", 1)
        prompt = PfpPrompt(
            prefix + "\n" + json.dumps(prompt.response_schema, separators=(",", ":")),
            json.dumps(public, ensure_ascii=False, separators=(",", ":")),
            prompt.response_schema,
        )
        return PreparedTaskTurn(task, prompt, "mining-structure-only-v1")

    @staticmethod
    def judges_for(spec):
        return ()

    @staticmethod
    def check_reply(spec, raw):
        return MiningContract.prepare_task(spec).check(raw)


def screen_mining(spec, raw, checked):
    """Reject answer-bearing/nongrounded guidance; never silently fall back to WF2."""
    if not checked["schema_valid"]:
        return dict(accepted=False, errors=["MINING_REPLY_SCHEMA"], candidates=[])
    answer = checked["answer"]
    errors = []
    retained = []
    seen = {}
    public_spec = deepcopy(spec)
    public_spec["input"] = stimulus(spec["input"])
    sources = operad_codec.source_texts(public_spec)
    slots = {row["id"] for row in operad_codec.catalogue()["slots"]}

    def text_screen(value, path=()):
        if type(value) is str and path[-2:] != ("source", "quote") and re.search(r"\d", value):
            errors.append("NUMERICAL_GUIDANCE_FORBIDDEN:" + "/".join(map(str, path)))
        elif type(value) is dict:
            for key, item in value.items():
                text_screen(item, (*path, key))
        elif type(value) is list:
            for index, item in enumerate(value):
                text_screen(item, (*path, index))

    text_screen(answer)
    ids = [op["id"] for op in answer["operad_candidates"]]
    if len(set(ids)) != len(ids):
        errors.append("DUPLICATE_MINED_OPERAD_ID")
    for index, op in enumerate(answer["operad_candidates"]):
        if op["arity"] != len(op["source_colours"]):
            errors.append("MINED_ARITY_MISMATCH:" + op["id"])
        if op["source"]["quote"] not in sources[op["source"]["kind"]]:
            errors.append("MINED_SOURCE_QUOTE_MISSING:" + op["id"])
        if set(op["witness_refs"]) - slots - {"task_result"}:
            errors.append("MINED_WITNESS_REF_UNKNOWN:" + op["id"])
        checksum = digest(canonical(op))
        row = dict(
            record=op,
            source_pointer=f"/answer/operad_candidates/{index}",
            duplicate_of=seen.get(checksum),
        )
        retained.append(row)
        seen.setdefault(checksum, row["source_pointer"])
    guidance = answer["l2_guidance"]
    if len({row["slot"] for row in guidance}) != len(guidance):
        errors.append("DUPLICATE_L2_GUIDANCE_SLOT")
    if spec["checker"] == "integer_sum_v1" and {row["slot"] for row in guidance} != SUM_L2:
        errors.append("MISSING_TASK_L2_GUIDANCE")
    for row in guidance:
        if row["source"]["quote"] not in sources[row["source"]["kind"]]:
            errors.append("L2_SOURCE_QUOTE_MISSING:" + row["slot"])
    return dict(accepted=not errors, errors=errors, candidates=retained)


def freeze_attachment(raw, checked, screening):
    if not screening["accepted"]:
        raise ValueError("WF3_MINING_NOT_SCREENED")
    payload = dict(
        schema="pfp.wf3.mined-attachment.v1",
        status="UNVERIFIED_MINED_CANDIDATES",
        operads=checked["answer"]["operad_candidates"],
        focus_slots=checked["answer"]["focus_slots"],
        failure_triggers=checked["answer"]["failure_triggers"],
        l2_guidance=checked["answer"]["l2_guidance"],
        mining_raw_sha256=digest(raw),
        provenance=[row["source_pointer"] for row in screening["candidates"]],
        authority_effect="None",
    )
    return dict(payload=payload, sha256=digest(canonical(payload)))


def verify_attachment(attachment):
    if (
        type(attachment) is not dict
        or set(attachment) != {"payload", "sha256"}
        or digest(canonical(attachment["payload"])) != attachment["sha256"]
    ):
        raise ValueError("WF3_ATTACHMENT_DIGEST_MISMATCH")
    return deepcopy(attachment)


def solver_attachment(attachment):
    """Bind full frozen custody by digest; expose the candidate operations and guidance compactly."""
    frozen = verify_attachment(attachment)
    payload = frozen["payload"]
    return dict(
        sha256=frozen["sha256"],
        operads=deepcopy(payload["operads"]),
        l2_guidance={row["slot"]: row["guidance"] for row in payload["l2_guidance"]},
    )


class SolverContract:
    WORKFLOW_ID = "WF3"
    FOLDER = "wf0003"
    VERSION = VERSION
    BASE_TEMPLATE = BASE_TEMPLATE
    ATTEMPT_ID = "wf0003-solver-1"
    SOURCE_FILES = COMMON_SOURCES + UPSTREAM_SOURCES
    COLLECTION_FILES = ("collection.json",)
    validate_task = staticmethod(validate_task)

    def __init__(self, attachment):
        self.attachment = verify_attachment(attachment)

    def prepare_task(self, spec):
        spec = validate_task(spec)
        instruction = (
            "WF3: licensed solve. Unverified mining. Typed JSON. slot_report keys: "
            + ",".join(row["id"] for row in operad_codec.catalogue()["slots"])
            + ". Use bound input facts. Short reasons; no execution claims."
        )
        case = deepcopy(spec["input"])
        case["pfp_mined_attachment"] = solver_attachment(self.attachment)
        task = PfpTaskPrompt(
            spec["task_id"],
            spec["seed_prompt"],
            case,
            solver_response_schema(spec, self.attachment["payload"]["operads"]),
        )
        base = yaml.safe_load(basic_task_template("").system)
        task_policy = dict(
            policy_id=base["semantic_policy_manifest"]["policy_id"],
            profile="bounded_task_turn",
            authority_effect="None",
            rules=[
                "Untrusted proposal; host verifies.",
                "Only declared finite operations licensed.",
                "No execution or admission claims.",
            ],
        )
        template = PfpPromptTemplate(
            json.dumps(task_policy, ensure_ascii=False, separators=(",", ":")) + "\n" + instruction,
            "[USER PROMPT]",
            {},
        )
        prompt = PreparePfpTaskTurnUseCase().execute(template, task, self.ATTEMPT_ID)
        prefix = template.system
        public = json.loads(prompt.user)
        public.pop("answer_schema")
        prompt = PfpPrompt(
            prefix + "\nSchema: response_format.",
            json.dumps(public, ensure_ascii=False, separators=(",", ":")),
            prompt.response_schema,
        )
        return PreparedTaskTurn(task, prompt, spec["checker"])

    @staticmethod
    def judges_for(spec):
        def check(case, answer):
            return integer_sum_judge(case, answer["task_result"])

        return (("wf0003:integer_sum_v1", check),) if spec["checker"] == "integer_sum_v1" else ()

    @staticmethod
    def finalize_check(spec, checked):
        public_spec = deepcopy(spec)
        public_spec["input"] = stimulus(spec["input"])
        result = structured.codec_check(public_spec, checked)
        if result["failure_class"] == "WF2_OPERAD_STRUCTURE":
            result["failure_class"] = "WF3_OPERAD_STRUCTURE"
        result.update(assess_l2(spec, result))
        if result["schema_valid"] and result["l2_grounding_valid"] is False:
            result.update(status="PROVIDER_COMPLETED", failure_class="WF3_L2_GROUNDING")
        return result

    def check_reply(self, spec, raw):
        checked = self.prepare_task(spec).check(
            raw, judges=self.judges_for(spec), require_checker=spec["checker"] != "schema_only"
        )
        return self.finalize_check(spec, checked)

    @staticmethod
    def collect_emitted(spec, raw, checked):
        result = operad_codec.collect_emitted(spec, raw, checked)
        result["workflow_id"] = "WF3"
        return result


def assess_l2(spec, checked):
    """Check public input bindings and explicit constraint declarations, not model execution."""
    if not checked["schema_valid"] or spec["checker"] != "integer_sum_v1":
        return dict(l2_grounding_valid=None, l2_errors=[], l2_checked_slots=[])
    rows = checked["answer"]["slot_report"]
    values = spec["input"]["values"]
    expected = {
        "concrete_spans": dict(source="input.values", literal=values),
        "parameter_bindings": dict(values=values, arithmetic="integer_exact"),
        "preservation_obligations": dict(
            all_operands_once=True, signed_integers=True, rounding="forbidden"
        ),
    }
    errors, valid = [], []
    for slot in sorted(SUM_L2):
        try:
            value = rows[slot]["value"]
            if slot == "instantiated_arguments":
                op_id = value.get("operad_id") if type(value) is dict else None
                ops = checked["answer"]["operad_candidates"]
                if not any(
                    op["id"] == op_id
                    and op["arity"] == 1
                    and op["source_colours"] == ["IntegerList"]
                    and op["target_colour"] == "Integer"
                    for op in ops
                ):
                    raise ValueError("UNBOUND_INTEGER_LIST_OPERATION")
                target = dict(operad_id=op_id, arguments=values)
            else:
                target = expected[slot]
            if canonical(value) != canonical(target):
                raise ValueError("PUBLIC_BINDING_OR_DECLARED_CONSTRAINT_MISMATCH")
            valid.append(slot)
        except (ValueError, KeyError, TypeError) as exc:
            errors.append("L2_GROUNDING:" + slot + ":" + str(exc))
    return dict(l2_grounding_valid=not errors, l2_errors=errors, l2_checked_slots=valid)
