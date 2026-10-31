"""WF4 contracts: explicit reference serialization, with no computed answer in P*."""

import json
from copy import deepcopy

import yaml

from pfp.domain.contracts.pfp_runtime import (
    PfpPrompt,
    PfpPromptTemplate,
    PfpTaskPrompt,
)
from pfp.infrastructure.adapters.pfp_campaign import canonical, digest
from pfp.infrastructure.task_turn import PreparedTaskTurn
from pfp.infrastructure.workflow_tasks import (
    BASE_TEMPLATE,
    basic_task_template,
    integer_sum_judge,
)
from pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase
from pfp.workflows.wf0002 import workflow as codec
from pfp.workflows.wf0003 import structured
from pfp.workflows.wf0003 import workflow as wf3
from adversary.infrastructure.lggr_adapter import LggrGluingAdapter

VERSION = "0.2.0"
SOURCE_FILES = (
    wf3.COMMON_SOURCES
    + wf3.UPSTREAM_SOURCES
    + (
        "workflows/wf0004/workflow.py",
        "workflows/wf0004/runner.py",
        "workflows/wf0004/workflow.json",
        "infrastructure/estimated_gateway.py",
        "workflows/measurement.py",
    )
)


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def validate_task(spec):
    spec = wf3.validate_task(spec)
    if spec["checker"] != "integer_sum_v1":
        raise ValueError("WF4_V1_REQUIRES_INTEGER_SUM_CHECKER")
    return spec


class MiningContract:
    WORKFLOW_ID, FOLDER, VERSION = "WF4_MINER", "wf0004", VERSION
    BASE_TEMPLATE, SOURCE_FILES, COLLECTION_FILES = BASE_TEMPLATE, SOURCE_FILES, ()
    ATTEMPT_ID = "wf0004-mining-1"
    validate_task = staticmethod(wf3.MiningContract.validate_task)
    judges_for = staticmethod(lambda spec: ())

    @staticmethod
    def prepare_task(spec):
        old = wf3.MiningContract.prepare_task(spec)
        prefix = old.prompt.system.rsplit("\n", 1)[0]
        prompt = PreparePfpTaskTurnUseCase().execute(
            PfpPromptTemplate(prefix, "[USER PROMPT]", {}), old.task, MiningContract.ATTEMPT_ID
        )
        public = json.loads(prompt.user)
        public.pop("answer_schema")
        prompt = PfpPrompt(
            prefix + "\n" + compact(prompt.response_schema), compact(public), prompt.response_schema
        )
        return PreparedTaskTurn(old.task, prompt, old.checker_id)

    @staticmethod
    def check_reply(spec, raw):
        return MiningContract.prepare_task(spec).check(raw)


def freeze_profile(spec, attachment):
    """Compiler-owned public facts; no output total or intermediate arithmetic."""
    spec = validate_task(spec)
    attachment = wf3.verify_attachment(attachment)
    ops = attachment["payload"]["operads"]
    schema = wf3.solver_response_schema(spec, ops)
    rows = {
        row["id"]: dict(
            disposition="unresolved",
            value="",
            reason="No witness supplied in this bounded profile.",
        )
        for row in codec.catalogue()["slots"]
    }
    core = dict(
        carrier="IntegerList -> Integer",
        equality_policy="Exact integer equality",
        operands="input.values",
        colours="IntegerList,Integer",
        operators=",".join(op["id"] for op in ops),
        terminal="task_result.total",
    )
    for key, value in core.items():
        rows[key] = dict(disposition="provided", value=value, reason="")
    for key in wf3.SUM_L2:
        rows[key] = deepcopy(schema["$defs"][key]["const"])
    payload = dict(
        schema="pfp.wf4.public-profile.v1",
        slot_report=rows,
        operad_candidates=deepcopy(ops),
        mining_sha256=attachment["sha256"],
        origin="HOST_COMPILED_PUBLIC_FACTS_AND_UNVERIFIED_MINING",
        authority_effect="None",
    )
    return dict(payload=payload, sha256=digest(canonical(payload)))


def verify_profile(profile):
    if (
        set(profile) != {"payload", "sha256"}
        or digest(canonical(profile["payload"])) != profile["sha256"]
    ):
        raise ValueError("WF4_PROFILE_DIGEST_MISMATCH")
    return deepcopy(profile)


class SolverContract:
    WORKFLOW_ID, FOLDER, VERSION = "WF4", "wf0004", VERSION
    BASE_TEMPLATE, SOURCE_FILES = BASE_TEMPLATE, SOURCE_FILES
    COLLECTION_FILES = ("collection.json",)
    validate_task = staticmethod(validate_task)

    def __init__(self, attachment, profile, agent):
        if type(agent) is not int or agent not in range(1, 6):
            raise ValueError("WF4_AGENT_OUT_OF_RANGE")
        self.attachment, self.profile = wf3.verify_attachment(attachment), verify_profile(profile)
        self.ATTEMPT_ID = f"wf0004-agent-{agent}"

    def prepare_task(self, spec):
        spec = validate_task(spec)
        if freeze_profile(spec, self.attachment) != self.profile:
            raise ValueError("WF4_PROFILE_LINEAGE_MISMATCH")
        ids = [op["id"] for op in self.profile["payload"]["operad_candidates"]]
        schema = structured.object_schema(
            dict(
                task_result=deepcopy(spec["answer_schema"]),
                profile_ref={"const": self.profile["sha256"]},
                values=dict(type="array", items=dict(type="integer")),
                operad_ids=dict(type="array", items={"enum": ids}, minItems=1, uniqueItems=True),
                ddc_moves=codec.response_schema(spec)["properties"]["ddc_moves"],
            )
        )
        # Same bounded SPK-001 P* policy projection as WF3. Full schema stays host-side;
        # a short exact wire contract replaces repeated constant metadata in the wire.
        policy_id = yaml.safe_load(basic_task_template("").system)["semantic_policy_manifest"][
            "policy_id"
        ]
        system = (
            f"P* {policy_id} bounded_task_turn. Untrusted proposal; host verifies. "
            "Only declared finite operations; no execution/admission claims. "
            "WF4 independent solve. Return JSON only: task_id,attempt_id,input_sha256 copied "
            "from input,answer:{task_result:{total:integer},profile_ref:string,values:integer[],"
            "operad_ids:string[],ddc_moves:[]}. Copy profile_ref and values; select mined operad IDs. "
            "profile_ref references ALL frozen slots; values binds their four L2 facts to input. "
            "Use every signed operand once, exact arithmetic, no rounding. Empty ddc_moves if none. "
            "Full operad slots: " + ",".join(row["id"] for row in codec.catalogue()["slots"])
        )
        context = dict(
            values=spec["input"]["values"],
            profile_ref=self.profile["sha256"],
            mined=wf3.solver_attachment(self.attachment),
        )
        # Binding covers the entire task schema and context, even when not duplicated on wire.
        task = PfpTaskPrompt(spec["task_id"], spec["seed_prompt"], context, schema)
        prompt = PreparePfpTaskTurnUseCase().execute(
            PfpPromptTemplate(system, "[USER PROMPT]", {}), task, self.ATTEMPT_ID
        )
        public = json.loads(prompt.user)
        public.pop("answer_schema")
        return PreparedTaskTurn(
            task,
            PfpPrompt(system, compact(public), prompt.response_schema),
            "wf4-local-reference-structure-v1",
        )

    def check_reply(self, spec, raw):
        checked = self.prepare_task(spec).check(
            raw, judges=self.judges_for(spec), require_checker=True
        )
        return self.finalize_check(spec, checked)

    @staticmethod
    def judges_for(spec):
        return (
            (
                "wf4-local-binding",
                lambda case, a: (
                    canonical(a["values"]) == canonical(spec["input"]["values"]),
                    "Public input binding only; global evaluator checks arithmetic.",
                ),
            ),
        )

    def finalize_check(self, spec, checked):
        errors = []
        if checked["schema_valid"]:
            a = checked["answer"]
            if canonical(a["values"]) != canonical(spec["input"]["values"]):
                errors.append("L2_PUBLIC_BINDING_MISMATCH")
            if type(a["task_result"]["total"]) is not int:
                errors.append("NON_NATIVE_INTEGER_RESULT")
            # Structural DDC validation reuses WF2 over an explicit host projection.
            view = deepcopy(checked)
            view["answer"] = dict(
                task_result=a["task_result"],
                slot_report=self.profile["payload"]["slot_report"],
                operad_candidates=self.profile["payload"]["operad_candidates"],
                ddc_moves=a["ddc_moves"],
            )
            projection = structured.codec_check(spec, view)
            errors.extend(projection.get("structure_errors", []))
        checked["local_green"] = checked["schema_valid"] and not errors
        checked["local_errors"] = errors
        checked["operad_structure_valid"] = checked["local_green"]
        checked["task_correct"] = None  # Task semantics belong to the independent global evaluator.
        if not checked["local_green"]:
            checked.update(status="PROVIDER_COMPLETED", failure_class="WF4_LOCAL_CONTRACT")
        return checked

    @staticmethod
    def collect_emitted(spec, raw, checked):
        collection = codec.collect_emitted(spec, raw, checked)
        collection["workflow_id"] = "WF4"
        a = checked.get("answer")
        refs = a.get("operad_ids", []) if type(a) is dict else []
        collection["operad_references"] = [
            dict(
                id=op,
                pointer=f"/answer/operad_ids/{i}",
                disposition="UNVERIFIED_REFERENCE" if checked["local_green"] else "QUARANTINED",
            )
            for i, op in enumerate(refs if type(refs) is list else [])
        ]
        collection["interpretation"] = (
            "References are not newly emitted operad records. Raw bytes retained."
        )
        return collection


def evaluate_global(spec, checks):
    """All five structural locals plus exact semantics and overlap agreement; no vote."""
    if len(checks) != 5:
        raise ValueError("WF4_REQUIRES_FIVE_LOCAL_CHECKS")
    local = {f"agent-{i}": int(row["local_green"]) for i, row in enumerate(checks, 1)}
    totals, task_checks = [], []
    for row in checks:
        if row["local_green"]:
            result = row["answer"]["task_result"]
            totals.append(result["total"])
            task_checks.append(integer_sum_judge(spec["input"], result)[0])
        else:
            totals.append(None)
            task_checks.append(False)
    correct = all(item is True for item in task_checks)
    agreement = all(value == totals[0] for value in totals) and totals[0] is not None
    green = all(local.values()) and correct and agreement
    lggr = LggrGluingAdapter().evaluate_boundary(local, int(green)).to_dict()
    return dict(
        global_green=green,
        task_correct=correct,
        overlap_agreement=agreement,
        totals=totals,
        task_checks=task_checks,
        task_claim_audit=dict(
            scope="PROPOSED_TOTALS_ONLY",
            checked=sum(local.values()),
            verified=sum(item is True for item in task_checks),
            false=sum(row["local_green"] and not item for row, item in zip(checks, task_checks)),
            unaudited_other_claims=None,
        ),
        lggr=lggr,
        selected_agent="agent-1" if green else None,
        selected_result=dict(total=totals[0]) if green else None,
        status="HOST_ACCEPTED" if green else "TYPED_REFUSAL",
        authority_effect="None",
    )
