"""Scripted WF5 miner and five-solver gateway used by offline drivers and the WF5 suite.

Every reply is scripted inside this process; none reaches a provider and none
is evidence of model capability. ``cost_usd`` is the scripted billing figure
(0 by default). AuthorityEffect: None.
"""

import json
from threading import Barrier, Lock

from adversary.domain.providers.attempt import AdmittedRequest, CompletionOutcome
from adversary.domain.providers.types import CandidateResponse, Provider
from operations.domain.rop.result import Ok

from pfp.infrastructure.adapters.pfp_campaign import canonical, digest
from pfp.infrastructure.workflow_accounting import EstimatedBudgetGateway
from pfp.workflows.scripted import SPEC
from pfp.workflows.wf0003.scripted import ScriptedInvariantError, mining_answer
from pfp.workflows.wf0005 import rewrite, runner, workflow


def factory_for(
    calls, *, wrong=False, unknown=False, bad_mining=False, bad_colour=False, bad_ref=False,
    cost_usd=0,
):
    barrier, lock = Barrier(5), Lock()

    def factory(root, model, tokens):
        class Scripted:
            unbudgeted_max_output_tokens = tokens

            def complete_result(self, request, **options):
                public = json.loads(request.user)
                miner = public["attempt_id"] == workflow.MiningContract.ATTEMPT_ID
                if not miner:
                    if public["objective"] != rewrite.lower(SPEC)["payload"]["wire"]:
                        raise ScriptedInvariantError("SCRIPTED_SOLVER_OBJECTIVE_MISMATCH")
                    with bound.ledger.transaction(bound.limit) as state:
                        if len(state["attempts"]) != 6:
                            raise ScriptedInvariantError("SCRIPTED_SOLVER_BEFORE_ALL_RESERVATIONS")
                    barrier.wait(timeout=15)
                with lock:
                    calls.append(public)
                    generation = f"wf5-fixture-{len(calls)}"
                if miner:
                    a = mining_answer()
                    if bad_colour:
                        a["operad_candidates"][0]["target_colour"] = "total"
                    if bad_ref:
                        a["operad_candidates"][0]["witness_refs"] = ["sum"]
                    a["operad_candidates"][0]["source"]["quote"] = (
                        "not in seed" if bad_mining else "<sum>"
                    )
                    for row in a["l2_guidance"]:
                        row["source"]["quote"] = "<sum>"
                else:
                    c = public["input"]
                    a = dict(
                        task_result=dict(total=39 if wrong else 38),
                        values=c["values"],
                        profile_ref=c["profile_ref"],
                        operad_ids=[c["mined"]["operads"][0]["id"]],
                        ddc_moves=[],
                    )
                content = workflow.wf4.compact(
                    {
                        **{k: public[k] for k in ("task_id", "attempt_id", "input_sha256")},
                        "answer": a,
                    }
                )
                cost = None if unknown else cost_usd
                wire = canonical(
                    dict(
                        id=generation,
                        choices=[dict(message=dict(content=content), finish_reason="stop")],
                        usage=dict(prompt_tokens=15, completion_tokens=25, cost=cost),
                    )
                )
                candidate = CandidateResponse(
                    content,
                    model,
                    "openrouter",
                    input_tokens=15,
                    output_tokens=25,
                    cost_usd=cost,
                    generation_id=generation,
                    transport="fixture",
                )
                return Ok(
                    CompletionOutcome(
                        candidate,
                        AdmittedRequest(
                            generation,
                            "",
                            "",
                            Provider.OPENROUTER,
                            model,
                            request,
                            tokens,
                            None,
                            None,
                        ),
                        reply_bytes=wire,
                    )
                )

        bound = EstimatedBudgetGateway(
            Scripted(),
            model=model,
            price=dict(
                catalog_sha256="fixture",
                row=dict(id=model, pricing={"prompt": "0.0000001", "completion": "0.00000032"}),
            ),
            limit_microusd=runner.read(root / "plan.json")["estimated_run_cap_microusd"],
            max_calls=6,
            accounting_path=root / "accounting.sqlite3",
            run_id="wf0005:" + root.resolve().name,
            objective_sha256=digest(canonical(SPEC)),
            max_output_tokens=tokens,
        )
        return bound

    return factory
