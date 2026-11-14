"""WF3 contracts; WF2's pinned pure codec is reused, never its runtime or state."""

import json
from copy import deepcopy
from importlib.resources import files

import yaml

from pfp.domain.contracts.pfp_runtime import (
    PfpPrompt,
    PfpPromptTemplate,
    PfpTaskPrompt,
)
from pfp.domain.pfp_ingress import strict_json
from pfp.infrastructure import operad_host
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
    """Attach the Rust host's screen of a mining reply. No rule is applied here."""
    if not checked["schema_valid"]:
        return dict(accepted=False, errors=["MINING_REPLY_SCHEMA"], candidates=[])
    answer = checked["answer"]
    public_spec = deepcopy(spec)
    public_spec["input"] = stimulus(spec["input"])
    report = operad_host.mining(
        catalogue=[row["id"] for row in operad_codec.catalogue()["slots"]],
        sources=operad_codec.source_texts(public_spec),
        checker=spec["checker"],
        answer=answer,
    )
    return dict(
        accepted=report["accepted"],
        errors=report["errors"],
        candidates=[
            dict(
                record=op,
                source_pointer=row["pointer"],
                duplicate_of=row["duplicate_of"],
                typed=row["typed"],
                licensed_as=row["licensed_as"],
            )
            for op, row in zip(answer["operad_candidates"], report["candidates"], strict=True)
        ],
    )


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
    """Attach the Rust host's recheck of the four L2 slots against the public input.

    The WF3 solver schema pins these slots to the same host-computed constants
    (see ``structured.answer_schema``), so a schema-valid reply always passes:
    this is a defence-in-depth recheck of the copied bindings, not evidence that
    the model grounded anything.
    """
    if not checked["schema_valid"] or spec["checker"] != "integer_sum_v1":
        return dict(l2_grounding_valid=None, l2_errors=[], l2_checked_slots=[])
    report = operad_host.grounding(
        checker=spec["checker"],
        values=spec["input"]["values"],
        slot_report=checked["answer"]["slot_report"],
        candidates=checked["answer"]["operad_candidates"],
    )
    return dict(
        l2_grounding_valid=report["valid"],
        l2_errors=report["errors"],
        l2_checked_slots=report["checked_slots"],
    )
