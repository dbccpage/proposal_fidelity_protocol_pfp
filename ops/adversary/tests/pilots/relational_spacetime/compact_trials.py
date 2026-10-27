"""Five bounded trials of the versioned compact PFP recipe; historical runs stay frozen."""

import argparse
import json
import math
import sqlite3
from pathlib import Path

from adversary.infrastructure.providers.openrouter_catalog import fetch_openrouter_catalog
from adversary.infrastructure.providers.wire import decode_reply
from pfp.infrastructure.adapters.pfp_derivation import (
    model_pricing,
    provider_result,
    replay_current_run,
)
from pfp.infrastructure.adapters.pfp_evidence import (
    canonical,
    digest,
    write_once,
)
from pfp.infrastructure.adapters.pfp_experiment import (
    PfpExperimentAdapter,
    wire_for,
)
from pfp.use_cases.pfp_derivation_loops import (
    DerivationLimits,
    run_derivation_loops,
)

from adversary.tests.pilots.relational_spacetime.tasks import BY_ID
from adversary.tests.pilots.relational_spacetime.tasks import MODEL
from adversary.tests.pilots.relational_spacetime.tasks import PILOTS
from adversary.tests.pilots.relational_spacetime.tasks import ROOT
from adversary.tests.pilots.relational_spacetime.baseline import refuse_without_checkout
from adversary.tests.pilots.relational_spacetime.baseline import fresh_run_output
from adversary.tests.pilots.relational_spacetime.baseline import require_campaign_checkout
from adversary.tests.pilots.relational_spacetime.parameter_trials import sources as previous_sources
from pfp.infrastructure.numbered_prompts import DEFAULT_RUN_ID, build_prompt

CAMPAIGN = DEFAULT_RUN_ID
EVIDENCE = PILOTS / "evidence" / CAMPAIGN
TEMPLATES = ROOT / "pfp/infrastructure/yaml/prompts/templates"
LIMITS = DerivationLimits(loops=3)


def sources():
    pins = previous_sources()
    paths = [
        ROOT / "pfp/infrastructure/numbered_prompts.py",
        *[
            Path(__file__).with_name(f"compact_{name}.py")
            for name in ("checks", "trials")
        ],
        *sorted(TEMPLATES.rglob("*.yaml")),
    ]
    pins["files"].update({p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in paths})
    return pins


def render(pilot, loop, context):
    prompt = build_prompt(pilot, loop, context, run_id=CAMPAIGN)
    prompt["experiment_decoding"] = {"temperature": 0, "seed": 20261012 + BY_ID[pilot]["number"]}
    return prompt


def observation(pilot, loop, prompt, result, context):
    """Pure interpretation used identically during live capture and offline replay."""
    from adversary.tests.pilots.relational_spacetime.compact_checks import evaluate
    from adversary.tests.pilots.relational_spacetime.compact_checks import negative_controls
    from adversary.tests.pilots.relational_spacetime.compact_checks import validate_workpad

    if loop == 2:
        verdict, packet = validate_workpad(pilot, prompt["prompt_id"], result["content"])
        next_context = {"workpad": packet} if packet is not None else {"workpad_missing": True}
        controls = {"scope": "WORKPAD_SCHEMA_ONLY", "finite_certificate_checked": False}
    else:
        verdict, packet = evaluate(pilot, prompt["prompt_id"], result["content"])
        controls = negative_controls(pilot, prompt["prompt_id"], packet)
        # Control output and its verdict never become treatment input.
        next_context = {} if loop == 1 else context
    return verdict, controls, next_context


def observe(pilot, loop, path, prompt, result, receipt, context):
    verdict, controls, next_context = observation(pilot, loop, prompt, result, context)
    write_once(path / "host_verdict.json", verdict)
    write_once(path / "negative_control.json", controls)
    write_once(path / "next_context.json", next_context)
    return next_context


def prepare(*, output=None, model=None):
    """Retain reviewable prompt instances and pin sources before any provider call."""
    root = EVIDENCE if output is None else fresh_run_output(output, model=model, pilots=list(BY_ID))
    selected_model = MODEL if output is None else model
    pins, previews = sources(), []
    for pilot in BY_ID:
        for loop in (1, 2, 3):
            prompt = render(pilot, loop, {"workpad_missing": True} if loop == 3 else {})
            path = root / "previews" / pilot / f"stage_{loop:02d}.json"
            write_once(path, prompt)
            wire = canonical(wire_for(prompt, selected_model))
            previews.append(
                {
                    "pilot_id": pilot,
                    "stage": loop,
                    "path": path.relative_to(root).as_posix(),
                    "prompt_sha256": digest(canonical(prompt)),
                    "request_sha256": digest(wire),
                    "user_utf8_bytes": len(prompt["user_prompt"].encode("utf-8")),
                }
            )
    write_once(
        root / "preflight.json",
        {
            "schema": "pfp.po035-compact-preflight.v1",
            "authority_effect": "None",
            "source_pins": pins,
            "previews": previews,
            "provider_calls": 0,
            "stage3_preview_scope": "Missing-workpad case; actual valid workpad unknown before dispatch",
            "maximum_provider_attempts": 15,
            "limits_per_pilot": vars(LIMITS),
            **({"model": selected_model, "request_profile": "ORIGINAL_PROMPT_PREVIEW_BEFORE_PFP"}
               if output is not None else {}),
        },
    )
    return previews


def run(pilots, *, output=None, model=None, preflight=None):
    require_campaign_checkout()
    if preflight is None:
        raise ValueError("PREFLIGHT_REQUIRED")
    prepared = Path(preflight).read_bytes()
    preview = json.loads(prepared)
    pins = sources()
    if preview["source_pins"] != pins or preview.get("model") != model:
        raise ValueError("PREFLIGHT_SOURCE_DRIFT")
    root = fresh_run_output(output, model=model, pilots=pilots)
    write_once(root / "preflight.json", prepared)
    # Public catalog discovery has its own bounded timeout; no prompts are sent.
    catalog = fetch_openrouter_catalog(timeout=20)
    row = model_pricing(catalog, model)
    profile = {"model": model, "ceiling_usd_per_token": "0", "selected_model": row}
    write_once(root / "catalog.json", catalog)
    write_once(root / "sources.json", pins)
    for name in pins["files"]:
        write_once(root / "source_snapshot" / name, (ROOT / name).read_bytes())
    terminals = []
    for pilot in pilots:
        if sources() != pins:
            raise ValueError("SOURCE_CHANGED_AFTER_FREEZE")
        port = PfpExperimentAdapter(
            pilot=pilot,
            folder=root / pilot,
            campaign=CAMPAIGN,
            model=model,
            pricing_sha256=digest(catalog),
            sources=pins,
            profile=profile,
            prompt_builder=render,
            observer=observe,
        )
        terminal = run_derivation_loops(port, LIMITS)
        terminals.append(terminal)
        print(
            json.dumps(
                {
                    k: terminal[k]
                    for k in (
                        "pilot_id",
                        "provider_calls",
                        "settled_calls",
                        "tokens",
                        "cost_microusd",
                        "terminal",
                    )
                }
            ),
            flush=True,
        )
        if terminal["terminal"] != "LOOP_LIMIT":
            break
    return terminals


def replay_complete_run(folder, pilot):
    """Replay this complete three-stage free-route contract; never skip missing runs.

    A partial/pending run is retained but requires reconciliation, not a synthetic
    successful replay. This deliberately avoids reimplementing historical stop policies.
    """

    def load(name):
        return dict(decode_reply((folder / name).read_bytes()))

    config, terminal, snapshot = (
        load("run.json"),
        load("terminal.json"),
        load("budget_snapshot.json"),
    )
    if (
        terminal["terminal"] != "LOOP_LIMIT"
        or set(snapshot["attempts"]) != {"1", "2", "3"}
        or any(r["state"] != "settled" for r in snapshot["attempts"].values())
    ):
        raise ValueError("PARTIAL_RUN_REQUIRES_RECONCILIATION")
    if (
        config["pilot_id"] != pilot
        or terminal["pilot_id"] != pilot
        or config["model"] != MODEL
        or config["campaign"] != CAMPAIGN
        or config["limits"] != vars(LIMITS)
        or terminal["limits"] != vars(LIMITS)
        or config["sources"] != sources()
    ):
        raise ValueError("SOURCE_OR_CONFIG_DRIFT")
    catalog = (EVIDENCE / "catalog.json").read_bytes()
    profile = {
        "model": MODEL,
        "ceiling_usd_per_token": "0",
        "selected_model": model_pricing(catalog, MODEL),
    }
    if config["pricing_sha256"] != digest(catalog) or load("pricing_profile.json") != profile:
        raise ValueError("PRICING_CUSTODY_MISMATCH")
    with sqlite3.connect(
        f"{(folder / 'budget.sqlite3').resolve().as_uri()}?mode=ro", uri=True
    ) as db:
        state = db.execute("SELECT state FROM provider_budget WHERE id=?", (pilot,)).fetchone()
    if state is None or json.loads(state[0]) != snapshot or snapshot["limit"] != LIMITS.microusd:
        raise ValueError("BUDGET_SNAPSHOT_MISMATCH")
    elapsed = terminal["elapsed_seconds"]
    if (
        type(elapsed) not in (int, float)
        or not math.isfinite(elapsed)
        or not 0 <= elapsed < LIMITS.seconds
    ):
        raise ValueError("INVALID_ELAPSED_TIME")
    if {p.name for p in folder.glob("loop_*")} != {"loop_01", "loop_02", "loop_03"}:
        raise ValueError("LOOP_INVENTORY_MISMATCH")
    context, rows, generation_ids = {}, [], set()
    for loop in (1, 2, 3):
        prefix = f"loop_{loop:02d}/"
        prompt = render(pilot, loop, context)
        wire = canonical(wire_for(prompt, MODEL))
        raw = (folder / prefix / "raw_reply.json").read_bytes()
        receipt = load(prefix + "provider_receipt.json")
        if (
            load(prefix + "prompt.json") != prompt
            or (folder / prefix / "request.json").read_bytes() != wire
            or receipt["raw_sha256"] != digest(raw)
            or receipt["request_sha256"] != digest(wire)
            or receipt["prompt_sha256"] != digest(canonical(prompt))
        ):
            raise ValueError("RECEIPT_DIGEST_MISMATCH")
        result = provider_result(raw, MODEL)
        if any(receipt[k] != v for k, v in result.items() if k != "content"):
            raise ValueError("PROVIDER_RECEIPT_MISMATCH")
        hold = len(wire) + 512 + prompt["max_output_tokens"]
        attempt = snapshot["attempts"][str(loop)]
        expected = dict(
            state="settled",
            reserved=0,
            token_hold=hold,
            sequence=loop,
            prompt_sha256=digest(canonical(prompt)),
            request_sha256=digest(wire),
            actual=result["cost_microusd"],
            tokens=result["tokens"],
            generation_id=result["generation_id"],
        )
        if (
            canonical(attempt) != canonical(expected)
            or result["cost_microusd"] != 0
            or result["tokens"] > hold
            or sum(r["tokens"] for r in rows) + hold > LIMITS.tokens
            or result["usage"]["completion_tokens"] > prompt["max_output_tokens"]
            or result["generation_id"] in generation_ids
        ):
            raise ValueError("ATTEMPT_ACCOUNTING_MISMATCH")
        if (
            receipt["stage_name"] != prompt["experiment_stage"]
            or type(receipt["elapsed_seconds"]) not in (int, float)
            or not math.isfinite(receipt["elapsed_seconds"])
            or not (rows[-1]["elapsed_seconds"] if rows else 0)
            <= receipt["elapsed_seconds"]
            <= elapsed
            or type(receipt["deadline_seconds"]) not in (int, float)
            or not math.isfinite(receipt["deadline_seconds"])
            or not 0 < receipt["deadline_seconds"] <= LIMITS.seconds
        ):
            raise ValueError("RECEIPT_STAGE_OR_TIME_MISMATCH")
        verdict, controls, context = observation(pilot, loop, prompt, result, context)
        if (
            load(prefix + "host_verdict.json") != verdict
            or load(prefix + "negative_control.json") != controls
            or load(prefix + "next_context.json") != context
        ):
            raise ValueError("VERDICT_OR_CONTEXT_MISMATCH")
        rows.append(receipt)
        generation_ids.add(result["generation_id"])
    if (
        terminal["context"] != context
        or terminal["completed_loops"] != 3
        or terminal["provider_calls"] != 3
        or terminal["settled_calls"] != 3
        or terminal["tokens"] != sum(r["tokens"] for r in rows)
        or terminal["tokens"] > LIMITS.tokens
        or type(terminal["cost_microusd"]) is not int
        or terminal["cost_microusd"] != 0
        or type(snapshot["spent"]) is not int
        or snapshot["spent"] != 0
        or snapshot["settlements"] != {}
    ):
        raise ValueError("TERMINAL_ACCOUNTING_MISMATCH")
    return {"pilot_id": pilot, "replayed_calls": 3, "new_provider_calls": 0}


def replay(pilots, *, output=None):
    require_campaign_checkout()
    if not pilots or len(set(pilots)) != len(pilots) or any(p not in BY_ID for p in pilots):
        raise ValueError("INVALID_PILOT_SET")
    if output is not None:
        root = Path(output)
        catalog = (root / "catalog.json").read_bytes()
        pins = json.loads((root / "sources.json").read_bytes())
        preflight = json.loads((root / "preflight.json").read_bytes())
        if preflight["source_pins"] != pins:
            raise ValueError("PREFLIGHT_SOURCE_DRIFT")
        if pins != sources() or any(
            digest((root / "source_snapshot" / name).read_bytes()) != sha
            for name, sha in pins["files"].items()
        ):
            raise ValueError("SOURCE_DRIFT")
        outputs = []
        for pilot in pilots:
            folder = root / pilot
            config = json.loads((folder / "run.json").read_bytes())
            profile = {"model": config["model"], "ceiling_usd_per_token": "0",
                       "selected_model": model_pricing(catalog, config["model"])}
            if (config["campaign"] != CAMPAIGN or config["limits"] != vars(LIMITS)
                    or preflight["model"] != config["model"]
                    or config["pricing_sha256"] != digest(catalog)
                    or json.loads((folder / "pricing_profile.json").read_bytes()) != profile):
                raise ValueError("PRICING_OR_CONFIG_DRIFT")
            outputs.append(replay_current_run(folder, pilot, config["model"], render, observe, pins))
        return outputs
    pins = json.loads((EVIDENCE / "sources.json").read_text(encoding="utf-8"))
    if pins != sources():
        raise ValueError("SOURCE_DRIFT")
    for name, sha in pins["files"].items():
        if digest((EVIDENCE / "source_snapshot" / name).read_bytes()) != sha:
            raise ValueError("SNAPSHOT_DRIFT")
    outputs = [replay_complete_run(EVIDENCE / pilot, pilot) for pilot in pilots]
    ids = [
        json.loads(path.read_text(encoding="utf-8"))["generation_id"]
        for pilot in pilots
        for path in (EVIDENCE / pilot).glob("loop_*/provider_receipt.json")
    ]
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_GENERATION_ACROSS_PILOTS")
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run", "replay"))
    parser.add_argument("--pilot", choices=tuple(BY_ID), action="append")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--preflight", type=Path, help="Source-bound preflight.json from prepare --output")
    args = parser.parse_args()
    refuse_without_checkout(parser)
    pilots = args.pilot or list(BY_ID)
    if args.action == "prepare":
        if args.output is not None and args.model is None:
            parser.error("Current preparation requires --model")
        print(json.dumps({"prepared_prompts": len(prepare(output=args.output, model=args.model)), "provider_calls": 0}))
    elif args.action == "run":
        if args.output is None or args.model is None or not args.pilot or args.preflight is None:
            parser.error("run requires --output NEW_DIRECTORY, --model, --pilot and --preflight")
        run(pilots, output=args.output, model=args.model, preflight=args.preflight)
    else:
        if args.output is not None and not args.pilot:
            parser.error("Current replay requires --pilot")
        print(json.dumps(replay(pilots, output=args.output)))


if __name__ == "__main__":
    main()
