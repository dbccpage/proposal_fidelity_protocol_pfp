"""Small rewrite/workpad/temperature comparisons using the canonical PFP port."""

import argparse
import json
import math
import sqlite3
import urllib.request
from decimal import Decimal
from functools import partial
from pathlib import Path

import jsonschema

from omega_engine_woland.infrastructure.providers.openrouter_catalog import fetch_openrouter_catalog
from omega_engine_woland.infrastructure.providers.wire import decode_reply
from omega_engine_pfp.infrastructure.adapters.pfp_derivation import (
    microusd,
    model_pricing,
    provider_result,
    replay_current_run,
)
from omega_engine_pfp.infrastructure.adapters.pfp_evidence import (
    canonical,
    digest,
    write_once,
)
from omega_engine_pfp.infrastructure.adapters.pfp_experiment import (
    PfpExperimentAdapter,
    wire_for,
)
from omega_engine_pfp.use_cases.pfp_derivation_loops import (
    DerivationLimits,
    run_derivation_loops,
)

from omega_engine_woland.tests.pilots.relational_spacetime.baseline import refuse_without_checkout
from omega_engine_woland.tests.pilots.relational_spacetime.baseline import fresh_run_output
from omega_engine_woland.tests.pilots.relational_spacetime.baseline import require_campaign_checkout
from omega_engine_woland.tests.pilots.relational_spacetime.baseline import sources as original_sources
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import MODEL as MODEL
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import PILOTS
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import ROOT
from omega_engine_woland.tests.pilots.relational_spacetime.finite_checks import evaluate
from omega_engine_woland.tests.pilots.relational_spacetime.finite_checks import negative_control
from omega_engine_woland.tests.pilots.relational_spacetime.trial_prompts import build_prompt
from omega_engine_woland.tests.pilots.relational_spacetime.trial_prompts import stage_config

CAMPAIGN = "po035_experiments_20261012"
EVIDENCE = PILOTS / "evidence" / CAMPAIGN
NEW_SOURCES = (
    "omega_engine_woland/tests/pilots/relational_spacetime/parameter_trials.py",
    "omega_engine_woland/tests/pilots/relational_spacetime/trial_prompts.py",
    "omega_engine_pfp/infrastructure/adapters/pfp_experiment.py",
    "omega_engine_woland/infrastructure/providers/openrouter_experiment_deadline.py",
    "omega_engine_woland/tests/pilots/relational_spacetime/decoding_controls.py",
)


def sources():
    result = original_sources()
    result["files"].update({path: digest((ROOT / path).read_bytes()) for path in NEW_SOURCES})
    return result


def config_for(experiment, loop):
    config = stage_config("temperature" if experiment == "logit" else experiment, loop)
    if experiment == "logit":
        config = {
            **config,
            "stage_name": "logit_control" if loop == 1 else "logit_variant",
            "temperature": 0.7,
        }
    return config


def render(pilot, loop, context, *, experiment):
    prompt = build_prompt(
        pilot, loop, context, experiment="temperature" if experiment == "logit" else experiment
    )
    config = config_for(experiment, loop)
    if experiment == "logit":
        from omega_engine_woland.tests.pilots.relational_spacetime.decoding_controls import (
            cached_tokenizer_path,
        )
        from omega_engine_woland.tests.pilots.relational_spacetime.decoding_controls import (
            format_only_logit_bias,
        )

        bias = format_only_logit_bias(cached_tokenizer_path().read_bytes())

        prompt["prompt_id"] = prompt["prompt_id"].replace("temperature", "logit")
        prompt["prompt_uri"] = prompt["prompt_uri"].replace("temperature", "logit")
        user = json.loads(prompt["user_prompt"])
        user["prompt_id"] = prompt["prompt_id"]
        prompt["user_prompt"] = canonical(user).decode("utf-8")
    prompt["max_output_tokens"] = config["max_output_tokens"]
    prompt["experiment_stage"] = config["stage_name"]
    prompt["stage_config"] = config
    prompt["experiment_decoding"] = {
        "temperature": config["temperature"],
        "seed": 20261012 + BY_ID[pilot]["number"],
    }
    if experiment == "logit":
        prompt["experiment_decoding"].update(thinking=None, logit_bias=bias if loop == 2 else {})
    return prompt


def observe(pilot, loop, path, prompt, result, receipt, context, *, experiment):
    next_context = json.loads(json.dumps(context))
    config = config_for(experiment, loop)
    if config["response_kind"] == "public_workpad":
        verdict = dict(
            schema_status="REFUSED",
            certificate_status="NOT_CHECKED",
            analytical_status="UNVERIFIED",
        )
        try:
            document = dict(decode_reply(result["content"].encode()))
            jsonschema.Draft202012Validator(prompt["response_schema"]).validate(document)
            verdict.update(schema_status="VALID", code="PUBLIC_WORKPAD_VALID")
            name = "draft" if config["stage_name"] == "workpad_draft" else "audit"
            next_context.setdefault("workpads", {})[name] = document
        except (ValueError, jsonschema.ValidationError) as exc:
            verdict["code"] = (
                "INVALID_JSON" if isinstance(exc, ValueError) else "WORKPAD_SCHEMA_VIOLATION"
            )
            next_context.setdefault("workpad_feedback", []).append(verdict["code"])
    else:
        verdict, envelope = evaluate(pilot, prompt["prompt_id"], result["content"])
        write_once(
            path / "negative_control.json", negative_control(pilot, prompt["prompt_id"], envelope)
        )
    write_once(path / "host_verdict.json", verdict)
    write_once(path / "next_context.json", next_context)
    # The single-shot control is never forwarded into the workpad treatment.
    return next_context


def fetch_logit_endpoints():
    """Refresh the original logit profile's public quote before any generation."""
    from omega_engine_woland.infrastructure.providers.openai_compat import OPENROUTER_BASE_URL
    from omega_engine_woland.tests.pilots.relational_spacetime.decoding_controls import LOGIT_MODEL

    request = urllib.request.Request(
        f"{OPENROUTER_BASE_URL}/models/{LOGIT_MODEL}/endpoints",
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read(8_000_001)


def run(experiment, pilots, *, output=None, model=None):
    require_campaign_checkout()
    from omega_engine_woland.tests.pilots.relational_spacetime.decoding_controls import LOGIT_MODEL
    from omega_engine_woland.tests.pilots.relational_spacetime.decoding_controls import (
        validate_logit_profile,
    )

    if experiment not in ("scratchpad", "temperature", "logit"):
        raise ValueError("UNKNOWN_EXPERIMENT")
    if experiment == "logit" and model != LOGIT_MODEL:
        raise ValueError("PINNED_LOGIT_MODEL_REQUIRED")
    root = fresh_run_output(output, model=model, pilots=pilots)
    raw_catalog = fetch_openrouter_catalog(timeout=20)
    catalog_path = root / f"catalog_{experiment}.json"
    write_once(catalog_path, raw_catalog)
    if experiment == "logit":
        endpoints = fetch_logit_endpoints()
        write_once(root / "qwen72_endpoints.json", endpoints)
        profile = validate_logit_profile(json.loads(raw_catalog), json.loads(endpoints))
    else:
        row = model_pricing(raw_catalog, model)
        profile = {"model": model, "ceiling_usd_per_token": "0", "selected_model": row}
    pins = sources()
    terminals = []
    for pilot in pilots:
        folder = root / experiment / pilot
        if (folder / "run.json").exists():
            raise ValueError("RUN_ALREADY_EXISTS_NO_AUTOMATIC_RETRY")
        adapter = PfpExperimentAdapter(
            pilot=pilot,
            folder=folder,
            campaign=f"{CAMPAIGN}:{experiment}",
            model=model,
            pricing_sha256=digest(raw_catalog),
            sources=pins,
            profile=profile,
            prompt_builder=partial(render, experiment=experiment),
            observer=partial(observe, experiment=experiment),
        )
        loops = 4 if experiment == "scratchpad" else 2
        terminal = run_derivation_loops(adapter, DerivationLimits(loops=loops))
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
            # Do not spend a new pilot budget after any uncertain infrastructure/cap failure.
            break
    return terminals


def replay(experiment, pilots, *, output=None):
    require_campaign_checkout()
    if output is not None:
        from omega_engine_woland.tests.pilots.relational_spacetime.decoding_controls import validate_logit_profile

        if experiment not in ("scratchpad", "temperature", "logit"):
            raise ValueError("UNKNOWN_EXPERIMENT")
        if not pilots or len(set(pilots)) != len(pilots) or any(p not in BY_ID for p in pilots):
            raise ValueError("INVALID_PILOT_SET")
        root = Path(output)
        catalog = (root / f"catalog_{experiment}.json").read_bytes()
        outputs = []
        for pilot in pilots:
            folder = root / experiment / pilot
            config = json.loads((folder / "run.json").read_bytes())
            profile = (validate_logit_profile(json.loads(catalog),
                       json.loads((root / "qwen72_endpoints.json").read_bytes()))
                       if experiment == "logit" else
                       {"model": config["model"], "ceiling_usd_per_token": "0",
                        "selected_model": model_pricing(catalog, config["model"])})
            if (config["campaign"] != f"{CAMPAIGN}:{experiment}"
                    or config["limits"] != vars(DerivationLimits(loops=4 if experiment == "scratchpad" else 2))
                    or config["pricing_sha256"] != digest(catalog)
                    or json.loads((folder / "pricing_profile.json").read_bytes()) != profile):
                raise ValueError("PRICING_OR_CONFIG_DRIFT")
            outputs.append(replay_current_run(folder, pilot, config["model"],
                partial(render, experiment=experiment), partial(observe, experiment=experiment), sources()))
        return outputs
    outputs = []
    for pilot in pilots:
        folder = EVIDENCE / experiment / pilot
        if not (folder / "run.json").exists():
            continue

        def load(name):
            return json.loads((folder / name).read_text(encoding="utf-8"))

        config, terminal, snapshot = (
            load("run.json"),
            load("terminal.json"),
            load("budget_snapshot.json"),
        )
        limits = DerivationLimits(**config["limits"])
        if (
            terminal["limits"] != config["limits"]
            or terminal["pilot_id"] != pilot
            or config["pilot_id"] != pilot
            or config["campaign"] != f"{CAMPAIGN}:{experiment}"
        ):
            raise ValueError("LIMIT_OR_ID_MISMATCH")
        elapsed = terminal["elapsed_seconds"]
        if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("INVALID_ELAPSED_TIME")
        profile = load("pricing_profile.json")
        if type(profile.get("ceiling_usd_per_token")) is not str:
            raise ValueError("INVALID_PRICING_PROFILE")
        rate = Decimal(profile["ceiling_usd_per_token"])
        if (
            not rate.is_finite()
            or rate < 0
            or rate * 120000 > Decimal("0.05")
            or profile.get("model", config["model"]) != config["model"]
        ):
            raise ValueError("INVALID_PRICING_PROFILE")
        with sqlite3.connect(
            f"{(folder / 'budget.sqlite3').resolve().as_uri()}?mode=ro", uri=True
        ) as connection:
            row = connection.execute(
                "SELECT state FROM provider_budget WHERE id=?", (pilot,)
            ).fetchone()
        if row is None or json.loads(row[0]) != snapshot:
            raise ValueError("BUDGET_SNAPSHOT_MISMATCH")
        model = config["model"]
        if config["sources"] != sources():
            raise ValueError("SOURCE_OR_MODEL_DRIFT")
        attempts = snapshot["attempts"]
        expected = {str(i) for i in range(1, len(attempts) + 1)}
        if set(attempts) != expected or snapshot["limit"] != limits.microusd:
            raise ValueError("ATTEMPT_SEQUENCE_OR_LIMIT_MISMATCH")
        unresolved = {key: row for key, row in attempts.items() if row["state"] != "settled"}
        if len(unresolved) > 1 or any(row["state"] != "reserved" for row in unresolved.values()):
            raise ValueError("UNSUPPORTED_ATTEMPT_STATE")
        context, receipts = {}, []
        for path in sorted(folder.glob("loop_*")):
            if not (path / "provider_receipt.json").exists():
                continue
            loop = len(receipts) + 1
            if path.name != f"loop_{loop:02d}":
                raise ValueError("LOOP_SEQUENCE_MISMATCH")
            prompt = render(pilot, loop, context, experiment=experiment)
            receipt = json.loads((path / "provider_receipt.json").read_text())
            raw, wire = (path / "raw_reply.json").read_bytes(), canonical(wire_for(prompt, model))
            if json.loads((path / "prompt.json").read_text(encoding="utf-8")) != prompt:
                raise ValueError("PROMPT_LINEAGE_MISMATCH")
            if (path / "request.json").read_bytes() != wire or any(
                (
                    receipt["raw_sha256"] != digest(raw),
                    receipt["request_sha256"] != digest(wire),
                    receipt["prompt_sha256"] != digest(canonical(prompt)),
                )
            ):
                raise ValueError("RECEIPT_DIGEST_MISMATCH")
            result = provider_result(raw, model)
            if any(receipt[k] != v for k, v in result.items() if k != "content"):
                raise ValueError("PROVIDER_RECEIPT_MISMATCH")
            hold = len(wire) + 512 + prompt["max_output_tokens"]
            reserved = microusd(rate * hold)
            attempt = attempts.get(str(loop), {})
            previous_elapsed = receipts[-1]["elapsed_seconds"] if receipts else 0
            receipt_elapsed = receipt["elapsed_seconds"]
            deadline = receipt["deadline_seconds"]
            if (
                type(receipt_elapsed) not in (int, float)
                or not math.isfinite(receipt_elapsed)
                or not previous_elapsed <= receipt_elapsed <= elapsed
                or type(deadline) not in (int, float)
                or not math.isfinite(deadline)
                or not 0 < deadline <= limits.seconds
                or receipt["stage_name"] != prompt["experiment_stage"]
            ):
                raise ValueError("RECEIPT_STAGE_OR_TIME_MISMATCH")
            if (
                attempt.get("state") != "settled"
                or attempt.get("sequence") != loop
                or attempt.get("token_hold") != hold
                or attempt.get("reserved") != reserved
                or attempt.get("actual") != result["cost_microusd"]
                or attempt.get("tokens") != result["tokens"]
                or attempt.get("generation_id") != result["generation_id"]
                or attempt.get("request_sha256") != receipt["request_sha256"]
                or attempt.get("prompt_sha256") != receipt["prompt_sha256"]
                or result["tokens"] > hold
                or result["cost_microusd"] > reserved
                or result["usage"]["completion_tokens"] > prompt["max_output_tokens"]
                or sum(row["tokens"] for row in receipts) + hold > limits.tokens
                or sum(row["cost_microusd"] for row in receipts) + reserved > limits.microusd
                or any(row["generation_id"] == result["generation_id"] for row in receipts)
            ):
                raise ValueError("ATTEMPT_ACCOUNTING_MISMATCH")
            context = observe(
                pilot, loop, path, prompt, result, receipt, context, experiment=experiment
            )
            receipts.append(receipt)
        settled = {key for key, row in attempts.items() if row["state"] == "settled"}
        if settled != {str(i) for i in range(1, len(receipts) + 1)}:
            raise ValueError("UNRECEIPTED_SETTLED_ATTEMPT")
        pending_error = None
        for key, attempt in unresolved.items():
            loop = len(receipts) + 1
            path = folder / f"loop_{loop:02d}"
            prompt = render(pilot, loop, context, experiment=experiment)
            wire = canonical(wire_for(prompt, model))
            hold = len(wire) + 512 + prompt["max_output_tokens"]
            reserved = microusd(rate * hold)
            if (
                key != str(loop)
                or attempt.get("sequence") != loop
                or attempt.get("token_hold") != hold
                or load(f"loop_{loop:02d}/prompt.json") != prompt
                or (path / "request.json").read_bytes() != wire
                or attempt.get("request_sha256") != digest(wire)
                or attempt.get("prompt_sha256") != digest(canonical(prompt))
                or sum(row["tokens"] for row in receipts) + hold > limits.tokens
                or sum(row["cost_microusd"] for row in receipts) + reserved > limits.microusd
            ):
                raise ValueError("PENDING_ATTEMPT_CUSTODY_MISMATCH")
            pending_error = load(f"loop_{loop:02d}/infrastructure_error.json")
            raw_path = path / "raw_reply.json"
            if pending_error.get("hold_retained") is not True or pending_error.get(
                "raw_sha256"
            ) != (digest(raw_path.read_bytes()) if raw_path.exists() else None):
                raise ValueError("PENDING_RAW_BINDING_MISMATCH")
            observed = pending_error.get("observed_unsettled_usage")
            if observed is not None:
                pending_result = provider_result(raw_path.read_bytes(), model)
                actual = {
                    "tokens": pending_result["tokens"],
                    "cost_microusd": pending_result["cost_microusd"],
                }
                if (
                    observed != actual
                    or attempt.get("observed") != actual
                    or attempt.get("tokens") != actual["tokens"]
                    or attempt.get("reserved") != max(reserved, actual["cost_microusd"])
                    or not (
                        pending_result["tokens"] > hold
                        or pending_result["cost_microusd"] > reserved
                        or pending_result["usage"]["completion_tokens"]
                        > prompt["max_output_tokens"]
                    )
                ):
                    raise ValueError("PENDING_OBSERVED_USAGE_MISMATCH")
            elif attempt.get("reserved") != reserved or attempt.get("tokens", 0) != 0:
                raise ValueError("PENDING_RESERVATION_MISMATCH")
            elif raw_path.exists():
                try:
                    pending_result = provider_result(raw_path.read_bytes(), model)
                except (ValueError, TypeError, KeyError):
                    pass
                else:
                    if pending_error.get("code") != "DUPLICATE_GENERATION" or not any(
                        row["generation_id"] == pending_result["generation_id"] for row in receipts
                    ):
                        raise ValueError("UNEXPLAINED_UNSETTLED_REPLY")
        expected_paths = {f"loop_{int(key):02d}" for key in attempts}
        if {path.name for path in folder.glob("loop_*")} != expected_paths:
            raise ValueError("UNRECORDED_LOOP_PATH")
        if terminal["context"] != context or terminal["settled_calls"] != len(receipts):
            raise ValueError("TERMINAL_CONTEXT_MISMATCH")
        if terminal["completed_loops"] != len(receipts) or len(snapshot["attempts"]) > limits.loops:
            raise ValueError("ATTEMPT_OR_COMPLETION_CEILING_MISMATCH")
        unresolved_cost = sum(
            a["reserved"] for a in snapshot["attempts"].values() if a["state"] != "settled"
        )
        unresolved_tokens = sum(
            a.get("tokens", 0) for a in snapshot["attempts"].values() if a["state"] != "settled"
        )
        if (
            terminal["tokens"] != sum(r["tokens"] for r in receipts) + unresolved_tokens
            or terminal["cost_microusd"]
            != sum(r["cost_microusd"] for r in receipts) + unresolved_cost
        ):
            raise ValueError("ACCOUNTING_MISMATCH")
        if snapshot["spent"] != terminal["cost_microusd"] or terminal["provider_calls"] != len(
            snapshot["attempts"]
        ):
            raise ValueError("LEDGER_MISMATCH")
        reason = terminal["terminal"]
        if reason == "LOOP_LIMIT":
            if (
                len(receipts) != limits.loops
                or unresolved
                or elapsed >= limits.seconds
                or terminal["tokens"] > limits.tokens
                or terminal["cost_microusd"] > limits.microusd
            ):
                raise ValueError("LOOP_LIMIT_MISMATCH")
        elif reason == "TIME_CAP":
            if elapsed < limits.seconds and not (
                pending_error
                and pending_error.get("code") == "TIME_CAP_BEFORE_DISPATCH"
                and elapsed >= limits.seconds - 2 * (limits.loops - len(receipts))
            ):
                raise ValueError("TIME_CAP_UNWITNESSED")
        elif reason in {"TOKEN_CAP", "COST_CAP"}:
            field = "tokens" if reason == "TOKEN_CAP" else "cost_microusd"
            ceiling = limits.tokens if reason == "TOKEN_CAP" else limits.microusd
            if terminal[field] < ceiling:
                if unresolved or len(receipts) >= limits.loops:
                    raise ValueError("RESOURCE_CAP_UNWITNESSED")
                next_prompt = render(pilot, len(receipts) + 1, context, experiment=experiment)
                next_hold = (
                    len(canonical(wire_for(next_prompt, model)))
                    + 512
                    + next_prompt["max_output_tokens"]
                )
                next_reservation = (
                    next_hold if reason == "TOKEN_CAP" else microusd(rate * next_hold)
                )
                if terminal[field] + next_reservation <= ceiling:
                    raise ValueError("RESOURCE_CAP_UNWITNESSED")
        elif reason == "INFRASTRUCTURE_ERROR":
            if not unresolved or pending_error is None:
                raise ValueError("INFRASTRUCTURE_STOP_UNWITNESSED")
        else:
            raise ValueError("UNSUPPORTED_TERMINAL")
        outputs.append(
            {"pilot_id": pilot, "replayed_calls": len(receipts), "terminal": terminal["terminal"]}
        )
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("run", "replay"))
    parser.add_argument("experiment", choices=("scratchpad", "temperature", "logit"))
    parser.add_argument("--pilot", choices=tuple(BY_ID), action="append")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model")
    args = parser.parse_args()
    refuse_without_checkout(parser)
    pilots = args.pilot or list(BY_ID)
    if args.action == "run":
        if args.output is None or args.model is None or not args.pilot:
            parser.error("run requires --output NEW_DIRECTORY, --model and --pilot")
        run(args.experiment, pilots, output=args.output, model=args.model)
    else:
        if args.output is not None and not args.pilot:
            parser.error("Current replay requires --pilot")
        print(json.dumps(replay(args.experiment, pilots, output=args.output)))


if __name__ == "__main__":
    main()
