"""Scripted WF3 miner and solver gateway used by offline drivers and the WF3-WF5 suites.

Every reply is scripted inside this process; none reaches a provider and none
is evidence of model capability. ``cost_usd`` is the scripted billing figure the
gateway reports (0 by default: a scripted reply costs nothing). AuthorityEffect: None.
"""

import json
from copy import deepcopy

from adversary.domain.providers.attempt import AdmittedRequest, CompletionOutcome
from adversary.domain.providers.types import CandidateResponse, Provider, thaw_json
from operations.domain.rop.result import Ok

from pfp.infrastructure.adapters.pfp_campaign import canonical, digest
from pfp.infrastructure.workflow_accounting import EstimatedBudgetGateway
from pfp.workflows.wf0002.scripted import candidate as wf2_answer
from pfp.workflows.wf0003 import workflow


class ScriptedInvariantError(RuntimeError):
    """A scripted gateway saw a request the workflow contract must never send."""


def mining_answer():
    return dict(
        operad_candidates=[
            dict(
                id="sum",
                operation="Sum the integer list without computing a result here.",
                source_colours=["IntegerList"],
                target_colour="Integer",
                arity=1,
                source=dict(kind="seed_prompt", quote="input.values"),
                witness_refs=["task_result"],
            )
        ],
        focus_slots=["concrete_spans", "parameter_bindings", "invariant_witnesses"],
        failure_triggers=["Reject floating point substitutes and preserve every input operand."],
        l2_guidance=[
            dict(
                slot=slot,
                source=dict(kind="seed_prompt", quote="input.values"),
                guidance="Bind the entire public signed integer list exactly once without rounding.",
            )
            for slot in sorted(workflow.SUM_L2)
        ],
    )


def solver_answer():
    answer = wf2_answer()
    answer["operad_candidates"] = deepcopy(mining_answer()["operad_candidates"])
    values = [17, 25, -4]
    bindings = dict(
        concrete_spans=dict(source="input.values", literal=values),
        parameter_bindings=dict(values=values, arithmetic="integer_exact"),
        instantiated_arguments=dict(operad_id="sum", arguments=values),
        preservation_obligations=dict(
            all_operands_once=True, signed_integers=True, rounding="forbidden"
        ),
    )
    for row in answer["slot_report"]:
        if row["slot"] in bindings:
            row["value"] = bindings[row["slot"]]
        row["reason"] = ""
    answer["slot_report"] = {row.pop("slot"): row for row in answer["slot_report"]}
    return answer


def reply(turn, answer):
    return json.dumps(
        {
            **{k: turn.binding[k] for k in ("task_id", "attempt_id", "input_sha256")},
            "answer": answer,
        },
        ensure_ascii=False,
    ).encode()


def factory_for(calls, *, bad_mining=False, unknown_cost=False, quote="input.values", cost_usd=0):
    def factory(root, model, tokens):
        class Scripted:
            unbudgeted_max_output_tokens = tokens

            def complete_result(self, request, **options):
                expected_format = (
                    "json_object"
                    if json.loads(request.user)["attempt_id"] == workflow.MiningContract.ATTEMPT_ID
                    else "json_schema"
                )
                if thaw_json(request.decoding.response_format)["type"] != expected_format:
                    raise ScriptedInvariantError("SCRIPTED_RESPONSE_FORMAT_MISMATCH")
                with gateway.ledger.transaction(gateway.limit) as state:
                    if not any(row["state"] == "reserved" for row in state["attempts"].values()):
                        raise ScriptedInvariantError("SCRIPTED_CALL_WITHOUT_RESERVATION")
                public = json.loads(request.user)
                calls.append(public)
                is_miner = public["attempt_id"] == workflow.MiningContract.ATTEMPT_ID
                answer = mining_answer() if is_miner else solver_answer()
                if is_miner:
                    answer["operad_candidates"][0]["source"]["quote"] = quote
                    if bad_mining:
                        answer["operad_candidates"][0]["operation"] = "The result is 38."
                content = json.dumps(
                    {
                        **{k: public[k] for k in ("task_id", "attempt_id", "input_sha256")},
                        "answer": answer,
                    }
                )
                wire = json.dumps(
                    dict(
                        id=f"fixture-{len(calls)}",
                        choices=[dict(message=dict(content=content))],
                        usage=dict(
                            prompt_tokens=15,
                            completion_tokens=25,
                            cost=None if unknown_cost else cost_usd,
                        ),
                    )
                ).encode()
                c = CandidateResponse(
                    content,
                    model,
                    "openrouter",
                    input_tokens=15,
                    output_tokens=25,
                    cost_usd=None if unknown_cost else cost_usd,
                    generation_id=f"fixture-{len(calls)}",
                    transport="fixture",
                )
                admitted = AdmittedRequest(
                    f"fixture-{len(calls)}",
                    "",
                    "",
                    Provider.OPENROUTER,
                    model,
                    request,
                    tokens,
                    None,
                    None,
                )
                return Ok(CompletionOutcome(c, admitted, reply_bytes=wire))

        gateway = EstimatedBudgetGateway(
            Scripted(),
            model=model,
            price=dict(
                catalog_sha256="fixture",
                row=dict(id=model, pricing={"prompt": "0.000000001", "completion": "0.000000001"}),
            ),
            limit_microusd=json.loads((root / "plan.json").read_text())[
                "estimated_run_cap_microusd"
            ],
            max_calls=json.loads((root / "plan.json").read_text())["maximum_new_provider_calls"],
            accounting_path=root / "accounting.sqlite3",
            run_id="test-wf3:" + root.name,
            objective_sha256=digest(canonical(json.loads((root / "task.json").read_text()))),
            max_output_tokens=tokens,
        )
        return gateway

    return factory
