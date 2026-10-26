"""One typed cochain repair using the original Woland run's remaining allowance.

Recipe cochain-certificate-repair-v1.0.0: replace an unverified prose artifact
with a typed mathematical proposal and an independent calculation. No expected
answer enters the prompt. This is a small derived task, not full C002 completion.
"""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path

from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
from omega_engine_pfp.infrastructure.estimated_gateway import (
    DurableRunGateway,
    create_accounted_openrouter_gateway,
)
from omega_engine_pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase
from omega_engine_pfp.use_cases.pfp_proposal import CheckPfpTaskTurnUseCase
from omega_engine_woland.infrastructure.live_openrouter_transport import default_pfp_model_port
from omega_engine_woland.infrastructure.providers.wire import decode_reply

RECIPE = "cochain-certificate-repair-v1.0.0"
EDGES = [[0, 1, 4], [1, 2, -7], [2, 3, 9], [3, 4, -3], [4, 5, 5], [0, 5, 8], [1, 4, -1], [2, 5, 11]]
ANSWER_SCHEMA = dict(type="object", additionalProperties=False,
    required=["potentials", "edge_residuals"], properties={
        "potentials": dict(type="array", minItems=6, maxItems=6, items=dict(type="integer")),
        "edge_residuals": dict(type="array", minItems=8, maxItems=8, items=dict(type="integer")),
    })


def check_certificate(case, answer):
    """Validate actual values and every witness equation; no stored answer equality."""
    if type(answer) is not dict or set(answer) != {"potentials", "edge_residuals"}:
        return dict(accepted=False, reason="CERTIFICATE_SHAPE")
    potential, reported = answer["potentials"], answer["edge_residuals"]
    if (type(potential) is not list or type(reported) is not list
            or len(potential) != case["vertices"] or len(reported) != len(case["edges"])
            or any(type(value) is not int for value in potential + reported)):
        return dict(accepted=False, reason="CERTIFICATE_TYPES")
    computed = [weight - (potential[v] - potential[u]) for u, v, weight in case["edges"]]
    accepted = potential[0] == 0 and computed == reported and all(value == 0 for value in computed)
    return dict(accepted=accepted, reason="EXACT" if accepted else "CERTIFICATE_EQUATIONS", computed_residuals=computed)


def run(state_path: Path, *, replay: bool):
    state = json.loads(state_path.read_bytes())
    output = state_path.parent
    record_path = output / "typed_repair.json"
    prior = (output / "cycle_certificate.json").read_bytes()
    task = PfpTaskPrompt(RECIPE,
        "Construct integer vertex potentials anchored at vertex zero whose differences match all oriented edge weights. "
        "Privately calculate along the directed chain, then recompute each redundant edge and every reported residual. "
        "The previous prose artifact failed the declared JSON shape and witness equations. Return the typed certificate only.",
        dict(vertices=6, edges=EDGES, anchor_vertex=0, anchor_value=0, rejected_proposal=prior.decode("utf-8")), ANSWER_SCHEMA)
    template = PfpPromptTemplate("Use exact integer arithmetic and preserve edge order. AuthorityEffect: None.",
                                 "[USER PROMPT]", ANSWER_SCHEMA)
    prepared = PreparePfpTaskTurnUseCase().execute(template, task, "typed-repair-1")
    action_id = "critique:" + sha256((task.challenge + "\0typed-repair-1").encode()).hexdigest()
    if replay:
        record = json.loads(record_path.read_bytes())
        raw = bytes.fromhex(record["raw_completion_hex"])
        if record["prepared"] != prepared.to_dict() or sha256(raw).hexdigest() != record["raw_completion_sha256"]:
            raise ValueError("REPLAY_BINDING_MISMATCH")
        budget = state["provider_binding"]["run_budget"]
        if DurableRunGateway.read_binding(budget["accounting_path"]) != budget:
            raise ValueError("ORIGINAL_BUDGET_BINDING_MISMATCH")
        wire = decode_reply(DurableRunGateway.read_raw_reply(budget["accounting_path"], action_id))
        if raw != wire["choices"][0]["message"]["content"].encode("utf-8"):
            raise ValueError("REPLAY_PROVIDER_WIRE_MISMATCH")
    else:
        if record_path.exists():
            raise ValueError("REPAIR_ALREADY_RECORDED: use --replay, never a fresh allowance")
        binding = state["provider_binding"]
        budget = binding["run_budget"]
        if budget["schema"] != "pfp.fuzzy-run.v1" or budget["limit_microusd"] > 50000:
            raise ValueError("ORIGINAL_FUZZY_BINDING_REQUIRED")
        if (budget["run_id"] != state["run_id"] or budget["objective_sha256"] !=
                sha256(state["objective"].encode("utf-8")).hexdigest()):
            raise ValueError("ORIGINAL_BUDGET_SCOPE_MISMATCH")
        # Missing custody must refuse before credentials or gateway creation can
        # accidentally replace the original run's exhausted allowance.
        if DurableRunGateway.read_binding(budget["accounting_path"]) != budget:
            raise ValueError("ORIGINAL_BUDGET_BINDING_MISMATCH")
        try:
            DurableRunGateway.read_action(budget["accounting_path"], action_id)
        except KeyError:
            pass
        else:
            raise ValueError("REPAIR_ACTION_ALREADY_CLAIMED: recover original custody without dispatch")
        gateway = create_accounted_openrouter_gateway(binding["model"], binding["max_output_tokens"],
            env_file=binding["env_file"], accounting_path=Path(budget["accounting_path"]),
            max_estimated_cost_microusd=budget["limit_microusd"], max_calls=budget["max_calls"],
            run_id=budget["run_id"], objective_sha256=budget["objective_sha256"])
        if gateway.binding != budget:
            raise ValueError("ORIGINAL_BUDGET_BINDING_MISMATCH")
        port = default_pfp_model_port(gateway=gateway, model=binding["model"])
        try:
            result = port.complete(prepared.system, prepared.user)
            raw = result.content.encode("utf-8")
            call_state = result.accounting_state
        except Exception as error:
            # A failed envelope still has its exact original vendor wire retained.
            wire = decode_reply(gateway.raw_reply(action_id))
            raw = wire["choices"][0]["message"]["content"].encode("utf-8")
            call_state = type(error).__name__
        record = dict(recipe=RECIPE, role="one typed repair after unverified prose; same original allowance",
            authority_effect="None", budget_binding=budget, prepared=prepared.to_dict(),
            prior_artifact_sha256=sha256(prior).hexdigest(), raw_completion_hex=raw.hex(),
            raw_completion_sha256=sha256(raw).hexdigest(), accounting_state=call_state)
    pfp = CheckPfpTaskTurnUseCase().execute(task, prepared, raw)
    record["pfp"] = pfp
    record["independent_judge"] = (check_certificate(task.case, pfp["answer"])
        if pfp["schema_valid"] else dict(accepted=False, reason="PFP_SCHEMA"))
    if not replay:
        record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    else:
        original = json.loads(record_path.read_bytes())
        # Compare the persisted host report's JSON representation. This does not
        # normalize or repair the retained model completion checked above.
        if json.loads(json.dumps(pfp)) != original["pfp"] or record["independent_judge"] != original["independent_judge"]:
            raise ValueError("REPLAY_JUDGEMENT_MISMATCH")
    return {"recipe": RECIPE, "replay": replay, "provider_calls": 0 if replay else 1,
            "pfp_schema_valid": pfp["schema_valid"], "independent_judge": record["independent_judge"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.state, replay=arguments.replay), indent=2))


if __name__ == "__main__":
    main()
