"""Versioned recipe learned from refused packets; original judges stay frozen.

An independently typed side channel accepts only safe lift requests and candidate
learning. It never repairs, accepts, or impersonates a malformed proposal packet.
"""

import argparse
import json
import math

import jsonschema
import yaml

from omega_engine_providers.infrastructure.openrouter_catalog import fetch_openrouter_catalog
from omega_engine_providers.infrastructure.wire import decode_reply
from omega_engine_symbol_game.infrastructure.adapters.pfp_derivation import (
    PfpDerivationAdapter,
    model_pricing,
    provider_result,
    replay_run,
)
from omega_engine_symbol_game.infrastructure.adapters.pfp_evidence import (
    canonical,
    digest,
    write_once,
)
from omega_engine_symbol_game.use_cases.pfp_derivation_loops import (
    DerivationLimits,
    run_derivation_loops,
)

from . import campaign as base
from .cases import (
    BY_ID,
    LIFTS,
    MODEL,
    PILOTS,
    ROOT,
    load,
    prompt_container,
    proposal_body,
    response_schema,
)
from .checking import evaluate, negative_control

CAMPAIGN = "po035_derivations_20261012_v2"
EVIDENCE = PILOTS / "evidence" / CAMPAIGN
SELF = "omega_engine_education/pfp/infrastructure/po035/adaptive.py"


def sources():
    result = base.sources()
    result["files"][SELF] = digest((ROOT / SELF).read_bytes())
    return result


def build_prompt(pilot, loop, context=None, *, final=False):
    prompt = prompt_container(pilot, loop, context, final=final)
    prompt["prompt_id"] += ":v2"
    prompt["prompt_uri"] += "/v2"
    user = json.loads(prompt["user_prompt"])
    user["prompt_id"] = prompt["prompt_id"]
    user["response_placement"] = {
        "root_fields_only": ["derived_under_policy", "summary", "process_integrity", "sections"],
        "sections": "Exactly one section with name po035_derivation and exactly one row.",
        "row_fields_all_required": [
            "prompt_id",
            "status",
            "derivation",
            "certificate",
            "requested_lifts",
            "learning",
        ],
        "summary": "Include narrowest_defensible_thesis, evidence_scope, next_concrete_test.",
        "process_integrity": "Include seed_allows_theory_refutation and should_continue booleans.",
        "scope": "Place every derivation, certificate, lift request and learning item inside that one row. Do not create multiple rows for fixtures. Do not put requested_lifts or learning at root. Recheck JSON delimiters before returning.",
    }
    if BY_ID[pilot]["number"] == 199:
        user["certificate_conventions"] = {
            "interval": "Use s_squared=c*c*t*t-sum(x_i*x_i). Apply the dilation to BOTH t and x, with c fixed. It does not change lattice pitch a.",
            "single_certificate": "The radius/interval fields concern the first point. Only null_envelope concerns the separately specified null point. Combine them in one certificate inside the single row.",
        }
    prompt["user_prompt"] = canonical(user).decode()
    prompt["recipe"] = CAMPAIGN
    return prompt


def ingress(pilot, content):
    """No parser repair: only valid JSON and independently validated existing fields."""
    try:
        document = decode_reply(content.encode())
    except ValueError:
        return [], [], None
    if document.get("derived_under_policy") != "SPK-001":
        return [], [], None
    locations = [("", document)]
    sections = document.get("sections")
    if type(sections) is list:
        for i, section in enumerate(sections):
            if (
                type(section) is not dict
                or section.get("name") != "po035_derivation"
                or type(section.get("rows")) is not list
            ):
                continue
            locations += [
                (f"/sections/{i}/rows/{j}", row)
                for j, row in enumerate(section["rows"])
                if type(row) is dict
            ]
    schema = response_schema(pilot)["properties"]["sections"]["items"]["properties"]["rows"][
        "items"
    ]["properties"]
    lifts, learning, previous = [], [], None
    for pointer, row in locations:
        for field, target in (("requested_lifts", lifts), ("learning", learning)):
            values = row.get(field)
            if type(values) is not list or len(values) > 15:
                continue
            for index, value in enumerate(values):
                if jsonschema.Draft202012Validator(schema[field]["items"]).is_valid(value):
                    target.append({"json_pointer": f"{pointer}/{field}/{index}", "value": value})
        if "derivation" in row and jsonschema.Draft202012Validator(schema["derivation"]).is_valid(
            row["derivation"]
        ):
            previous = {"derivation": row["derivation"], "json_pointer": f"{pointer}/derivation"}
    return lifts, learning, previous


def stage(pilot, loop, name, input_doc, output):
    path = base.capsule(pilot, loop, name) / "v2"
    write_once(path / "input.yaml", yaml.safe_dump(input_doc, sort_keys=False).encode())
    write_once(path / "response.yaml", yaml.safe_dump(output, sort_keys=False).encode())


def ordered_receipt(result, receipt):
    # Original provider usage key order is recovered from retained raw bytes.
    # Canonical JSON receipts sort keys; YAML stage bytes retain insertion order.
    ordered = {
        key: value
        for key, value in result.items()
        if key not in ("content", "_host_execution_kind")
    }
    ordered.update(
        {
            key: receipt[key]
            for key in ("raw_sha256", "prompt_sha256", "request_sha256", "elapsed_seconds")
        }
    )
    return ordered


def replay_base_observer(pilot, loop, path, prompt, result, receipt, context):
    return base.observe(
        pilot, loop, path, prompt, result, ordered_receipt(result, receipt), context
    )


def observe(pilot, loop, path, prompt, result, receipt, context):
    receipt = ordered_receipt(result, receipt)
    verdict, envelope = evaluate(pilot, prompt["prompt_id"], result["content"])
    requested, observations, previous = ingress(pilot, result["content"])
    common = dict(
        pilot_id=pilot,
        prompt_id=prompt["prompt_id"],
        loop=loop,
        raw_reply_sha256=receipt["raw_sha256"],
        authority_effect="None",
        source_packet_status=verdict["schema_status"],
        execution_kind=result.get("_host_execution_kind", "LIVE"),
    )
    stage(
        pilot,
        loop,
        "proposal",
        prompt,
        {**common, "provider_status": "PROVIDER_COMPLETED", "receipt": receipt},
    )
    grants = sorted(
        set(context.get("granted_lifts", []))
        | {item["value"]["id"] for item in requested if item["value"]["id"] in LIFTS}
    )
    stage(
        pilot,
        loop,
        "lift_grant",
        {**common, "typed_requests": requested},
        {
            **common,
            "granted": {key: LIFTS[key] for key in grants},
            "denied": [row for row in requested if row["value"]["id"] not in LIFTS],
            "ingress_scope": "Independent lift-item typing only; proposal packet verdict unchanged. Added assumptions license a conditional theorem.",
        },
    )
    stage(pilot, loop, "witness_check", common, {**common, **verdict})
    control = negative_control(pilot, prompt["prompt_id"], envelope)
    control["baseline_certificate_accepted"] = verdict["certificate_status"] == "HOST_ACCEPTED"
    stage(pilot, loop, "negative_control", common, {**common, **control})
    learning = []
    for i, observation in enumerate(observations):
        item = observation["value"]
        learning.append(
            {
                **common,
                **item,
                "json_pointer": observation["json_pointer"],
                "artifact_id": f"{pilot}:v2:loop{loop:02d}:{item['kind']}:{i:02d}",
                "prompt_text_sha256": digest(prompt["user_prompt"].encode()),
                "original_seed_sha256": prompt["original_seed_sha256"],
                "status": "CANDIDATE",
                "admitted": False,
                "analytical_status": "UNVERIFIED",
                "observed_certificate_status": verdict["certificate_status"],
                "negative_control": control,
            }
        )
    guidance = context.get("guidance", []) + [
        {key: item[key] for key in ("artifact_id", "kind", "text", "failure_or_gain")}
        for item in learning
    ]
    seen, selected = set(), []
    for item in reversed(guidance):
        if item["text"] not in seen:
            selected.append(item)
            seen.add(item["text"])
        if len(selected) == 10:
            break
    if envelope:
        body = proposal_body(envelope)
        previous = {"derivation": body["derivation"], "certificate": body["certificate"]}
    if previous:
        previous.update(prompt_id=prompt["prompt_id"], raw_reply_sha256=receipt["raw_sha256"])
    next_context = dict(
        parent_prompt_id=prompt["prompt_id"],
        granted_lifts=grants,
        feedback=verdict,
        guidance=list(reversed(selected)),
        previous_proposal=previous,
    )
    write_once(path / "candidate_learning.json", learning)
    write_once(path / "host_verdict.json", verdict)
    write_once(path / "lift_ingress.json", requested)
    stage(
        pilot,
        loop,
        "learning_refinement",
        common,
        {**common, "candidate_artifacts": learning, "next_context": next_context},
    )
    return next_context


def limits_for(pilot):
    prior = base.EVIDENCE / pilot / "terminal.json"
    if not prior.exists():
        return DerivationLimits(), None
    receipt = load(prior)
    if receipt["provider_calls"] >= 5:
        raise ValueError("PILOT_LOOP_LIMIT_ALREADY_REACHED")
    # Conservatively share the original pilot's ceilings across the failed recipe and revision.
    limits = DerivationLimits(
        loops=5 - receipt["provider_calls"],
        microusd=50_000 - receipt["cost_microusd"],
        tokens=120_000 - receipt["tokens"],
        seconds=180 - math.ceil(receipt["elapsed_seconds"]),
    )
    return limits, {
        "path": prior.relative_to(ROOT).as_posix(),
        "sha256": digest(prior.read_bytes()),
    }


def run(pilot):
    limits, prior = limits_for(pilot)
    raw = fetch_openrouter_catalog(timeout=20)
    row = model_pricing(raw, MODEL)
    root = EVIDENCE / pilot
    write_once(root / "catalog.json", raw)
    write_once(root / "pricing.json", row)
    write_once(root / "prior_budget.json", {"prior_run": prior, "remaining_limits": vars(limits)})
    write_once(
        PILOTS / pilot / "p_star_v2.yaml",
        yaml.safe_dump(build_prompt(pilot, 1), sort_keys=False, allow_unicode=True).encode(),
    )
    port = PfpDerivationAdapter(
        pilot=pilot,
        folder=root,
        campaign=CAMPAIGN,
        model=MODEL,
        pricing_sha256=digest(raw),
        sources=sources(),
        prompt_builder=build_prompt,
        observer=observe,
    )
    result = run_derivation_loops(port, limits)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "pilot_id",
                    "terminal",
                    "settled_calls",
                    "tokens",
                    "cost_microusd",
                    "elapsed_seconds",
                )
            }
        ),
        flush=True,
    )


def harvest_prior(pilot):
    """Offline extraction from the completed recipe: no new calls or retroactive grants."""
    root = base.EVIDENCE / pilot
    catalog = (root / "catalog.json").read_bytes()
    if load(root / "pricing.json") != model_pricing(catalog, MODEL) or load(root / "run.json")[
        "pricing_sha256"
    ] != digest(catalog):
        raise ValueError("PRIOR_PRICING_BINDING_MISMATCH")
    original = replay_run(
        root, pilot, MODEL, prompt_container, replay_base_observer, base.sources()
    )
    context, bindings = {}, []
    for path in sorted(root.glob("loop_*")):
        if not (path / "provider_receipt.json").exists():
            continue
        loop = int(path.name.split("_")[1])
        prompt, receipt = load(path / "prompt.json"), load(path / "provider_receipt.json")
        result = provider_result((path / "raw_reply.json").read_bytes(), MODEL)
        result["_host_execution_kind"] = "POSTHOC_TYPED_SIGNAL_HARVEST"
        context = observe(
            pilot, loop, EVIDENCE / pilot / path.name, prompt, result, receipt, context
        )
        bindings.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "receipt_sha256": digest((path / "provider_receipt.json").read_bytes()),
            }
        )
    harvest = dict(
        pilot_id=pilot,
        evidence_kind="POSTHOC_TYPED_SIGNAL_HARVEST",
        replayed_calls=original["replayed_calls"],
        context=context,
        bindings=bindings,
        sources=sources(),
        new_provider_calls=0,
        limitation="Grants were extracted after the run and enter only the final prompt; earlier provider requests did not see them.",
    )
    write_once(EVIDENCE / pilot / "harvest.json", harvest)
    return harvest


def replay():
    rows = []
    for pilot in BY_ID:
        if (base.EVIDENCE / pilot / "terminal.json").exists():
            rows.append(harvest_prior(pilot))
            continue
        root = EVIDENCE / pilot
        raw = (root / "catalog.json").read_bytes()
        if load(root / "pricing.json") != model_pricing(raw, MODEL) or load(root / "run.json")[
            "pricing_sha256"
        ] != digest(raw):
            raise ValueError("PRICING_BINDING_MISMATCH")
        limits, prior = limits_for(pilot)
        if load(root / "prior_budget.json") != {
            "prior_run": prior,
            "remaining_limits": vars(limits),
        } or load(root / "run.json")["limits"] != vars(limits):
            raise ValueError("PRIOR_BUDGET_BINDING_MISMATCH")
        rows.append(replay_run(root, pilot, MODEL, build_prompt, observe, sources()))
    return rows


def consolidate():
    replayed = replay()
    findings, candidates = [], []
    for row in replayed:
        pilot = row["pilot_id"]
        root = EVIDENCE / pilot
        original_root = (
            base.EVIDENCE / pilot
            if row.get("evidence_kind") == "POSTHOC_TYPED_SIGNAL_HARVEST"
            else root
        )
        learning, proposals, verdicts = [], [], []
        for path in sorted(original_root.glob("loop_*")):
            if not (path / "provider_receipt.json").exists():
                continue
            learning += load(root / path.name / "candidate_learning.json")
            prompt = load(path / "prompt.json")
            content = base.decode_provider_content(path / "raw_reply.json")
            verdict, envelope = evaluate(pilot, prompt["prompt_id"], content)
            verdicts.append({"prompt_id": prompt["prompt_id"], **verdict})
            if envelope:
                proposals.append(
                    {
                        "prompt_id": prompt["prompt_id"],
                        "raw_sha256": digest((path / "raw_reply.json").read_bytes()),
                        **proposal_body(envelope),
                    }
                )
            else:
                _, _, partial = ingress(pilot, content)
                if partial:
                    proposals.append(
                        {
                            "prompt_id": prompt["prompt_id"],
                            "raw_sha256": digest((path / "raw_reply.json").read_bytes()),
                            "source_packet_status": "REFUSED",
                            "analytical_status": "UNVERIFIED",
                            **partial,
                        }
                    )
        candidates += learning
        tags = [
            {key: item[key] for key in ("artifact_id", "kind", "text", "failure_or_gain")}
            for item in learning
        ]
        final = build_prompt(pilot, 6, row["context"] | {"guidance": tags}, final=True)
        final.update(
            tag_status="CANDIDATE_UNADMITTED",
            candidate_artifact_ids=[item["artifact_id"] for item in learning],
            candidate_artifacts_sha256=digest(canonical(learning)),
            analytical_status="UNVERIFIED",
            lineage_receipts=[
                path.relative_to(ROOT).as_posix()
                for path in sorted(original_root.glob("loop_*/provider_receipt.json"))
            ],
        )
        write_once(
            EVIDENCE / "final_prompts" / f"{pilot}.yaml",
            yaml.safe_dump(final, sort_keys=False, allow_unicode=True).encode(),
        )
        findings.append(
            dict(
                pilot_id=pilot,
                source_obligations=BY_ID[pilot]["obligations"],
                terminal=load(original_root / "terminal.json"),
                signal_extraction_kind=row.get("evidence_kind", "LIVE"),
                verdicts=verdicts,
                model_derivation_proposals=proposals,
                candidate_count=len(learning),
                analytical_status="UNVERIFIED",
            )
        )
    write_once(EVIDENCE / "candidate_artifacts.json", candidates)
    write_once(
        EVIDENCE / "consolidated_findings.json",
        {"authority_effect": "None", "pilots": findings, "candidate_policy_admissions": 0},
    )
    write_once(
        EVIDENCE / "replay.json",
        {"status": "REPLAY_VERIFIED", "pilots": replayed, "sources": sources()},
    )
    print(
        json.dumps(
            {
                "replayed_calls": sum(row["replayed_calls"] for row in replayed),
                "final_prompts": 5,
                "candidate_artifacts": len(candidates),
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=list(BY_ID))
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--consolidate", action="store_true")
    args = parser.parse_args()
    if args.run:
        run(args.run)
    elif args.consolidate:
        consolidate()
    elif args.replay:
        print(json.dumps(replay()))
    else:
        parser.error("Choose --run PILOT, --replay or --consolidate")


if __name__ == "__main__":
    main()
