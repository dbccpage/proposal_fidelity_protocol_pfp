"""WF5's own bindings, using WF4's read-only typed reference and LGGR components."""

import json
from copy import deepcopy

from pfp.domain.contracts.pfp_runtime import (
    PfpPrompt,
    PfpPromptTemplate,
    PfpTaskPrompt,
)
from pfp.infrastructure.task_turn import PreparedTaskTurn
from pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase
from pfp.workflows.wf0003 import workflow as wf3
from pfp.workflows.wf0004 import workflow as wf4

from . import rewrite

VERSION = "0.2.0"
SOURCE_FILES = tuple(
    dict.fromkeys(
        (
            *wf4.SOURCE_FILES,
            "workflows/wf0004/runner.py",
            "domain/tower/grammar.py",
            "domain/tower/golden_corpus.py",
            "workflows/wf0005/workflow.py",
            "workflows/wf0005/runner.py",
            "workflows/wf0005/rewrite.py",
            "workflows/wf0005/packet.ebnf",
            "workflows/wf0005/workflow.json",
            "workflows/wf0005/grammar_provenance.json",
        )
    )
)
DECODER_INSTRUCTION = "PFP packet: sum is exact addition; once uses all values; pN is positive N, nN negative N; total names the output."
validate_task = wf4.validate_task


class MiningContract:
    WORKFLOW_ID, FOLDER, VERSION = "WF5_MINER", "wf0005", VERSION
    BASE_TEMPLATE, SOURCE_FILES, COLLECTION_FILES = wf4.BASE_TEMPLATE, SOURCE_FILES, ()
    ATTEMPT_ID = "wf0005-mining-1"
    validate_task = staticmethod(wf3.MiningContract.validate_task)
    judges_for = staticmethod(lambda spec: ())

    @staticmethod
    def prepare_task(spec):
        # The shared mining runtime stores checker=schema_only. Its source task
        # remains the single declared integer-sum family; root admission checks it.
        original = deepcopy(spec)
        original["checker"] = "integer_sum_v1"
        bundle = rewrite.lower(original)
        rewritten = rewrite.rewritten_task(original, bundle)
        old = wf4.MiningContract.prepare_task(rewritten)
        prefix = old.prompt.system.rsplit("\n", 1)[0] + "\n" + DECODER_INSTRUCTION
        prefix += " Typed signature must be source_colours [IntegerList], target_colour Integer, arity one. total is an output FIELD, never a colour."
        prefix += " Return exactly one operation. witness_refs must be exactly [task_result]."
        schema = deepcopy(old.task.answer_schema)
        properties = schema["properties"]["operad_candidates"]["items"]["properties"]
        for name, value in dict(
            source_colours=["IntegerList"],
            target_colour="Integer",
            arity=1,
            witness_refs=["task_result"],
        ).items():
            properties[name] = {"const": value}
        schema["properties"]["operad_candidates"].update(minItems=1, maxItems=1)
        properties["source"]["properties"]["kind"] = {"const": "seed_prompt"}
        properties["source"]["properties"]["quote"] = {"enum": ["sum", "<sum>"]}
        for record in (schema["properties"]["l2_guidance"]["items"],):
            record["properties"]["source"]["properties"]["kind"] = {"const": "seed_prompt"}
            record["properties"]["source"]["properties"]["quote"] = {
                "enum": ["sum", "<sum>", "exact", "once", "values"]
            }
        task = PfpTaskPrompt(
            old.task.challenge,
            old.task.task_text,
            {**old.task.case, "rewrite_ref": bundle["sha256"]},
            schema,
        )
        prompt = PreparePfpTaskTurnUseCase().execute(
            PfpPromptTemplate(prefix, "[USER PROMPT]", {}), task, MiningContract.ATTEMPT_ID
        )
        public = json.loads(prompt.user)
        public.pop("answer_schema")
        return PreparedTaskTurn(
            task,
            PfpPrompt(
                prefix + "\nSchema: response_format.",
                wf4.compact(public),
                prompt.response_schema,
            ),
            "mining-structure-only-v1",
        )

    @staticmethod
    def check_reply(spec, raw):
        return MiningContract.prepare_task(spec).check(raw)


class SolverContract(wf4.SolverContract):
    WORKFLOW_ID, FOLDER, VERSION = "WF5", "wf0005", VERSION
    SOURCE_FILES = SOURCE_FILES

    def __init__(self, attachment, profile, bundle, agent):
        super().__init__(attachment, profile, agent)
        self.rewrite = deepcopy(bundle)
        self.ATTEMPT_ID = f"wf0005-agent-{agent}"

    def prepare_task(self, spec):
        task_spec = rewrite.rewritten_task(spec, self.rewrite)
        old = super().prepare_task(task_spec)
        context = deepcopy(old.task.case)
        # The profile already binds the full mined attachment. Replace its
        # redundant wire digest with the checked rewrite lineage, not another allowance.
        context["mined"].pop("sha256")
        context["rewrite_ref"] = self.rewrite["sha256"]
        task = PfpTaskPrompt(
            old.task.challenge, old.task.task_text, context, old.task.answer_schema
        )
        system = old.prompt.system.replace("WF4 independent solve.", "WF5 independent solve.")
        system += "\n" + DECODER_INSTRUCTION
        prompt = PreparePfpTaskTurnUseCase().execute(
            PfpPromptTemplate(system, "[USER PROMPT]", {}), task, self.ATTEMPT_ID
        )
        public = json.loads(prompt.user)
        public.pop("answer_schema")
        return PreparedTaskTurn(
            task,
            PfpPrompt(system, wf4.compact(public), prompt.response_schema),
            "wf5-local-reference-structure-v1",
        )

    def finalize_check(self, spec, checked):
        result = super().finalize_check(rewrite.rewritten_task(spec, self.rewrite), checked)
        if result["failure_class"] == "WF4_LOCAL_CONTRACT":
            result["failure_class"] = "WF5_LOCAL_CONTRACT"
        return result

    @staticmethod
    def collect_emitted(spec, raw, checked):
        collection = wf4.SolverContract.collect_emitted(spec, raw, checked)
        collection["workflow_id"] = "WF5"
        return collection


freeze_profile = wf4.freeze_profile
evaluate_global = wf4.evaluate_global
